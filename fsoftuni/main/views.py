from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied

from xhtml2pdf import pisa  
from io import BytesIO
from django.http import HttpResponse
from rich.pretty import pprint as pp
from students.models import StudentRecord

def html_to_pdf(html):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        # return result
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def cert(request, data=None):
  
    print("HERE ON CERT!!!!")
    d={
        "full_name":"CAEL POGI",
        "degree": "Master of Science",
        "department": "Yarn",
        "cgpa": "4576434567",
        "date": "Yesterday",
        "year": "2022",
    }
    if not data:
        data = d

    html = render_to_string('certs/cert.html', data, request=request)
    pdf = html_to_pdf(html)
        
        # rendering the template
    # return HttpResponse(pdf, content_type='application/pdf')
    return pdf
    # return render(request, 'cert.html', data) 

def exam_result(request, id):
    r = StudentRecord.objects.filter(id=id).first()
    if not request.user == r.student or not r.publish:
        raise PermissionDenied()
    
    html = render_to_string('certs/exam_result.html', {'res':r, 'not_demo':True}, request=request)
    pdf = html_to_pdf(html)
    print()
    return pdf


