import json
import os
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render , redirect
from django.contrib.auth import login , authenticate , logout 
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import custom_user
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from firebase_admin import auth,firestore,storage
from datetime import datetime
days = [{'name':'sunday','index':'0'},{'name':'monday','index':'1'},{'name':'tuesday','index':'2'},{'name':'wednesday','index':'3'},{'name':'thursday','index':'4'},{'name':'friday','index':'5'},{'name':'saturday','index':'6'}]
sch_days = [{'name':'sunday','slot':{'begin':'','end':''}},{'name':'monday','slot':{'begin':'','end':''}},{'name':'tuesday','slot':{'begin':'','end':''}},{'name':'wednesday','slot':{'begin':'','end':''}},{'name':'thursday','slot':{'begin':'','end':''}},{'name':'friday','slot':{'begin':'','end':''}},{'name':'saturday','slot':{'begin':'','end':''}}]
available_tests = ['Complete Blood Count (CBC)','Glucose Test','Liver Function Tests','Kidney Function Tests','Lipid Profile','Thyroid Function Tests','Urine Test','Prostate-Specific Antigen (PSA) Test','Cholesterol Test','Hemoglobin Test','Vitamin D Test','Iron Test','Calcium Test','Potassium Test','Uric Acid Test','Protein Test','Pregnancy Test','Cardiac Enzymes Test','Allergy test','Viral Tests (e.g., Hepatitis B, Hepatitis C, HIV)']
db = firestore.client()
# Create your views here.
def home(request):
   if request.user.is_authenticated and request.user.type=="('lab', 'Laboratory')":
      return HttpResponseRedirect(reverse('lab_dashboard')) 
   if request.user.is_authenticated and request.user.type =="('doctor', 'Doctor')":
      return HttpResponseRedirect(reverse('doc_dashboard')) 
   return HttpResponseRedirect(reverse('lab_login')) 
def doc_login(request):
   if request.user.is_authenticated and request.user.type == "('doctor', 'Doctor')":
      return render(request , 'doctor-dashboard.html')
   if request.method == 'POST':
            uid = request.POST['uid'] or None
            password = request.POST['password']
            # Optionally, create a user in Django's auth system if needed
            if uid:
             try:
              username = custom_user.objects.get(firebase_id=uid).username
              user = authenticate(request,username=username,password=password)
             except Exception as e: 
               user = None
             if user is not None:
              login(request,user)
              return HttpResponseRedirect(reverse('doc_dashboard'))
             else:
                return render(request , 'doctor-login.html', {'message':"wrong credentials"})
            else:
             return render(request , 'doctor-login.html', {'message':"wrong credentials"})
   else:
         return render(request , 'doctor-login.html')
  
def doc_register(request):
    if request.user.is_authenticated:
       return HttpResponseRedirect(reverse('doc_dashboard'))
    if request.method=='POST':
       type = ('doctor','Doctor')
       speciality = request.POST['Speciality']
       name = request.POST['name']
       phone_num = request.POST['mob_number']
       email = request.POST['email']
       password = request.POST['password']
       location = request.POST['location']
       # signup on firebase
       user_record = auth.create_user(
                email=email,
                password=password,
            )
       firebase_uid = user_record.uid
       # create user localy
       user = custom_user.objects.create_user(type = type , speciality = speciality, username = name ,email = email,password = password , phone_num = phone_num , location = location, firebase_id = firebase_uid)
       user.save()
       authen = authenticate( username = name , password = password)
       # create doctor's doc on firebase
       data = {
          'name':user.username,
          'specialityRef':user.speciality,
          'willayaRef':user.location,
          'phoneNumber':user.phone_num
       }
       doc = db.collection('doctors').document(user.firebase_id)
       doc.set(data)
       return HttpResponseRedirect(reverse('doc_dashboard'))
    willayas = db.collection('willaya').stream()
    willaya_data = []
    for willaya in willayas:
          willaya_dict = willaya.to_dict()
          willaya_data.append(willaya_dict) 
    return render(request , 'doctor-register.html',{'willayas':willaya_data})
def doc_dashboard(request):
   if request.user.is_authenticated and request.user.type== "('doctor', 'Doctor')":
    app_ref = db.collection('appointment')
    quary = app_ref.where('doctorRef','==',request.user.firebase_id)
    appointments = quary.stream()

    # Collect patient data
    data = []
    for appointment in appointments:
        appId = appointment.id
        appointment_dict = appointment.to_dict()
        timestamp = appointment_dict.get('timestamp')  # Assuming 'date_time' is the timestamp field
        if not timestamp:
            date_time = timestamp.replace(tzinfo=pytz.UTC).astimezone(tz=None)  # Convert Firestore timestamp to datetime
            appointment_dict['date'] = date_time.strftime('%Y-%m-%d')  
            appointment_dict['time'] = date_time.strftime('%H:%M %p')
        user_id = appointment_dict['userRef']
        patient_ref = db.collection('users').document(user_id).get()
        patient_dict = patient_ref.to_dict()
        data.append((patient_dict,appId,appointment_dict))
    return render(request , 'doctor-dashboard.html',{'data':data})
   return HttpResponseRedirect(reverse('doc_login'))
   
   
      

def doc_sch_time(request):
   if not request.user.is_authenticated:
      return HttpResponseRedirect(reverse('home'))
   if request.method=="POST":
    begin = request.POST['begin']
    end = request.POST['end']
    data = {
       'docRef':request.user.firebase_id,
       'dayIndex':request.POST['dayIndex'],
       'begin':begin,
       'end':end
    }
    insert = db.collection('docTime') 
    insert.add(data) 
   timeRef = db.collection('docTime').where('docRef','==',request.user.firebase_id).stream()
   data = []
   slotRef = []
   for day in sch_days:
    day['slot']['begin'] = ''
    day['slot']['end'] = ''
   for time in timeRef:
      time_dic = time.to_dict()
      sch_days[int(time_dic['dayIndex'])]['slot']['begin']=time_dic['begin']
      sch_days[int(time_dic['dayIndex'])]['slot']['end']=time_dic['end']
      sch_days[int(time_dic['dayIndex'])]['slotRef'] = time.id

   return render(request,'doctor-schedule-timings-page.html',{'days':sch_days})
def doc_logout(request):
   logout(request)
   return HttpResponseRedirect(reverse('doc_login'))
def lab_login(request):
  if request.user.is_authenticated and request.user.type=="('labo', 'Laoratory')":
      return HttpResponseRedirect(reverse('lab_dashboard'))
  if request.method == 'POST':
            uid = request.POST['uid'] or None
            password = request.POST['password']
            # Optionally, create a user in Django's auth system if needed
            if uid:
             try:
              username = custom_user.objects.get(firebase_id=uid).username
              user = authenticate(request,username=username,password=password)
              if user.type!="('lab', 'Laboratory')":
                 logout(request)
                 return render(request , 'Laboratories-login.html', {'message':"wrong credentials"})
             except Exception as e: 
               user = None
             if user is not None:
              login(request,user)
              return HttpResponseRedirect(reverse('lab_dashboard'))
             else:
                return render(request , 'Laboratories-login.html', {'message':"wrong credentials"})
            else:
             return render(request , 'Laboratories-login.html', {'message':"wrong credentials"})
   
  return render(request ,'Laboratories-login.html')
def lab_logout(request):
   logout(request)
   return HttpResponseRedirect(reverse('home'))
def lab_register(request):
   if request.user.is_authenticated and request.user.type == "('labo', 'Laoratory')":
      return HttpResponseRedirect(reverse('lab_dashboard'))
   if request.method=='POST':
       type = ('lab','Laboratory')
       name = request.POST['name']
       phone_num = request.POST['mob_number']
       email = request.POST['email']
       password = request.POST['password']
       location = request.POST['location']
       # signup on firebase
       user_record = auth.create_user(
                email=email,
                password=password,
            )
       firebase_uid = user_record.uid
       # create user localy
       user = custom_user.objects.create_user(type = type , speciality = "", username = name ,email = email,password = password , phone_num = phone_num , location = location, firebase_id = firebase_uid)
       user.save()
       authen = authenticate( username = name , password = password)
       # create doctor's doc on firebase
       data = {
          'name':user.username,
          'location':user.location,
          'phoneNumber':user.phone_num
       }
       doc = db.collection('laboratory').document(user.firebase_id)
       doc.set(data)
       return HttpResponseRedirect(reverse('lab_login'))
   willayas = db.collection('willaya').stream()
   willaya_data = []
   for willaya in willayas:
          willaya_dict = willaya.to_dict()
          willaya_data.append(willaya_dict) 
   return render(request,'lab-regester.html',{'willayas':willaya_data})
def lab_dashboard(request):
    if not request.user.is_authenticated:
      return HttpResponseRedirect(reverse('lab_login'))
    app_ref = db.collection('appointmentLab') 
    quary = app_ref.where('labRef','==',request.user.firebase_id)
    appointments = quary.stream()

    # Collect patient data
    data = []
    for appointment in appointments:
        appId = appointment.id 
        appointment_dict = appointment.to_dict()
        user_id = appointment_dict['userRef']
        patient_ref = db.collection('users').document(user_id).get()
        patient_dict = patient_ref.to_dict()
        data.append((patient_dict,appId,appointment_dict))
    return render(request,'Laboratories-dashboard.html',{'data':data})
def tests(request):
   if request.user.is_authenticated:
    if request.method=="POST":
       data = {
          'laboRef':request.user.firebase_id,
          'name':request.POST['test_added']
       }
       set_in = db.collection('tests')
       set_in.add(data)
    tests = db.collection('tests').where('laboRef','==',request.user.firebase_id).stream()
    tests_data = []
    for test in tests:
      test_dict = test.to_dict()
      tests_data.append(test_dict)
    test_data_arr = [item['name'] for item in tests_data]
    filtered_test_data = [test for test in available_tests if test not in test_data_arr]
    
    return render(request,'laboratories-avaible-analyses.html',{'tests':tests_data,'available_tests':filtered_test_data})

def lab_sch(request):
   if not request.user.is_authenticated:
      return HttpResponseRedirect(reverse('home')) 
   workingDaysIndexes = []
   labRef = []
   labTimes = db.collection('labTime').where('labRef','==',request.user.firebase_id).stream()
   for labTime in labTimes:
      labTime_dict = labTime.to_dict()
      workingDaysIndexes.append(labTime_dict['dayIndex'])
      labRef.append(labTime.id)
   availableDays = [{'name':day['name'],'index':day['index']} for day in days if day['index'] not in workingDaysIndexes]
   workingDays = [{'name':day['name'],'index':day['index'],'id':labRef[workingDaysIndexes.index(day['index'])]} for day in days if day['index']  in workingDaysIndexes]

   return render(request,'laboratories-schedule-timings.html',{'availableDays':availableDays,'workingDays':workingDays})
def lab_send_analysis(request):
   if not request.user.is_authenticated:
      return HttpResponseRedirect(reverse('home'))
   app_ref = db.collection('appointmentLab')
   quary = app_ref.where('labRef','==',request.user.firebase_id)
   appointments = quary.stream()

    # Collect patient data
   data = []
   for appointment in appointments:
        appId = appointment.id 
        appointment_dict = appointment.to_dict()
        user_id = appointment_dict['userRef']
        patient_ref = db.collection('users').document(user_id).get()
        patient_dict = patient_ref.to_dict()
        data.append((patient_dict,patient_ref.id))
   return render(request,'laboratories-send-result-analisis.html',{'users':data})
class UploadResultView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        file = request.FILES['file']
        userRef = request.POST['userRef']
        file_extension = os.path.splitext(file.name)[1]  # Get the file extension
        new_file_name = f"{userRef}{file_extension}"

        bucket = storage.bucket()
        blob = bucket.blob(new_file_name)

        blob.upload_from_file(file)  

        return JsonResponse({'message': 'File uploaded successfully', 'file_name': new_file_name})

