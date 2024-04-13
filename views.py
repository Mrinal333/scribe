import json
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render
from .key import google_api_key, openai_api_key
from django.views.decorators.http import require_POST
import requests
from .models import Summary

def home(request):
    return render(request, 'index.html')

@require_POST
def validate_and_save(request):
    text = request.POST.get("text", "")
    if text != "":
        response_size = request.POST.get('response_size', 100)
        cleaned_text = '\n'.join(line for line in text.splitlines() if line.strip())
        cleaned_text += f"\nSummarize the given data in {response_size} words like a doctor's note. And compulsorily Upper Case only the important points or key terms in the summary."
        
        choice = request.POST.get('summary_option','openai')
        if choice == "openai":
            url = "https://api.openai.com/v1/completions"
            headers = {'Authorization': f'Bearer {openai_api_key}'}
            data = {'prompt': cleaned_text, 'max_tokens': int(response_size), 'model': 'gpt-3.5-turbo-instruct-0914'} 
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['text'].strip()
                with open('summary.txt', 'w') as file:
                    file.write(generated_text)
                ob = Summary()
                ob.patient_data = cleaned_text
                ob.summarized_text = generated_text 
                ob.model = "OpenAi"
                ob.save()
                return JsonResponse({'generated_text': generated_text})
            else:
                error_message = response.json().get('error', 'Unknown error occurred')
                print(error_message)
                return JsonResponse({'error': error_message}, status=500)
        elif choice == "gemini":
            data = {
                'contents': [{
                    'parts': [{'text': cleaned_text}]
                }]
            }

            headers = {
                'Content-Type': 'application/json'
            }

            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={google_api_key}'
            response = requests.post(url, headers=headers, data=json.dumps(data))

            if response.status_code == 200:
                result = response.json()
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                
                with open('summary.txt', 'w') as file:
                    file.write(generated_text)
                
                ob = Summary()
                ob.patient_data = cleaned_text
                ob.summarized_text = generated_text 
                ob.model = "Gemini"
                ob.save()
                
                return JsonResponse({'generated_text': generated_text})
            else:
                error_message = response.json().get('error', 'Unknown error occurred')
                print(error_message)
                return JsonResponse({'error': error_message}, status=500)

    return JsonResponse({'error': 'Text cannot be empty'}, status=400)

@require_POST
def summary(request):
    return FileResponse(open('summary.txt', 'rb'), as_attachment=True)

def history(request):
    return render(request, "history.html", {"objects": Summary.objects.all()})