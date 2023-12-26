from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import problems,testcase
import docker,subprocess
from time import time
# Create your views here.
def signin(request):
    return render(request, 'signin.html')

def add_user(request):
    if request.method == "POST":
        username,emailid,pass1,pass2 = request.POST['username'],request.POST['email'],request.POST['pass1'],request.POST['pass2']
        if pass1==pass2:
            new_user = User.objects.create(username=username,email=emailid,password=pass1)
            new_user.save()
        return redirect('judge:login_page_url')
    else:
        return render(request,'signin.html')
    
def login_page(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        u = authenticate(request,username=username,password=password)
        if u is not None:
            login(request,u)
            print('logged in')
            return HttpResponse('successfully logged in')
        else:
            context = {'msg' : 'username or password is not correct'}
            return render(request,'login.html',context)
    return render(request,'login.html')
        

@login_required(login_url='login_page/')
def home(request):
    problem_list = problems.objects.all()
    user = request.user
    context = {'list' : problem_list,'user':user}
    return render(request,'home.html',context)

@login_required(login_url='../login_page/')
def description(request,id):
    problem = problems.objects.get(id = id)
    context={'problem':problem}
    return render(request,'description.html',context)

@login_required(login_url='../../login_page/')
def verdict(request,id):
    if request.method=='POST':
        docker_client = docker.from_env()
        Running = "running"
        problem = problems.objects.get(id=id)
        tc = testcase.objects.get(prob_id=id)
        print(tc)
        #replacing \r\n by \n in original output to compare it with the usercode output
        tc.output = tc.output.replace('\r\n','\n').strip() 

        verdict = "Wrong Answer" 
        res = ""
        run_time = 0

        user_code,language = request.POST['code'],request.POST['language']

        filename = 'user_code'
        file = filename + '.py'
        filepath = file

        cont_name = 'python_compiler'
        extension = '.py'
        docker_img = 'python'
        exe = f"python {filename}.py"
        clean = f"{filename} {filename}.c"
        compile = 'python'

        code = open(filepath,"w")
        code.write(user_code)
        print('user code : ',user_code)
        code.close()

        try:
            container = docker_client.containers.get(cont_name)
            container_state = container.attrs['State']
            container_is_running = (container_state['Status'] == Running)
            if not container_is_running:
                subprocess.run(f"docker start {cont_name}",shell=True)
        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {cont_name} {docker_img}",shell=True)

        c=subprocess.run(f"docker cp {filepath} {cont_name}:/{file}",shell=True)
        print(c)
        # compiling the code
        cmp = subprocess.run(f"docker exec {cont_name} {compile}", capture_output=True, shell=True)
        print(cmp)
        if cmp.returncode != 0:
            verdict = "Compilation Error"
            subprocess.run(f"docker exec {cont_name} rm {file}",shell=True)

        else:
            # running the code on given input and taking the output in a variable in bytes
            start = time()
            try:
                c = f'docker exec {cont_name} sh -c "echo {tc.input}| {exe}" '

                res = subprocess.run(c,capture_output=True, timeout=2, shell=True)
                print(c)
                run_time = time()-start
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)
            except subprocess.TimeoutExpired:
                run_time = time()-start
                verdict = "Time Limit Exceeded"
                subprocess.run(f"docker container kill {cont_name}", shell=True)
                subprocess.run(f"docker start {cont_name}",shell=True)
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)

            print(res.stdout,res.stderr,res.returncode,sep='\n')
            if verdict != "Time Limit Exceeded" and res.returncode != 0:
                verdict = "Runtime Error"

        user_stderr = ""
        user_stdout = ""
        if verdict == "Compilation Error":
            user_stderr = cmp.stderr.decode('utf-8')
        
        elif verdict == "Wrong Answer":
            user_stdout = res.stdout.decode('utf-8')
            print('output:',user_stdout)
            if str(user_stdout)==str(tc.output):
                verdict = "Accepted"
            tc.output += '\n' # added extra line to compare user output having extra ling at the end of their output
            if str(user_stdout)==str(tc.output):
                verdict = "Accepted"

        return HttpResponse(verdict)
    return HttpResponse('still building')
def logout_user(request):
    logout(request)
    return redirect('judge:login_page_url')