from django.shortcuts import render
from django.template.loader import render_to_string
from xhtml2pdf import pisa  
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from rich.pretty import pprint as pp
import pdfkit
from django.views.generic import View
from django.core.files.base import ContentFile
from io import StringIO
from wagtail.documents import get_document_model

# def html_to_pdf():
#     template_src='cert.html'
#     context_dict={
#         "full_name":"CAEL POGI",
#         "degree": "PEDIGREE",
#         "department": "psyhc",
#         "cgpa": "4576434567",
#         "date": "Yesterday"
#     }
#     template = get_template(template_src)
#     html  = template.render(context_dict)
#     result = BytesIO()
#     pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
#     if not pdf.err:
#         return HttpResponse(result.getvalue(), content_type='application/pdf')
#     return None

# con = {
#     "full_name":"CAEL POGI",
#     "degree": "PEDIGREE",
#     "department": "psyhc",
#     "cgpa": "4576434567",
#     "date": "Yesterday"
# }

# html = render_to_string('cert.html', con)


# pp(pdfkit.__dict__)

# with open('certkoto.html', 'w+') as f:
#     f.write(html)
#     pdf = html_to_pdf()
#     print(pdf)
#     print('----------------------')
#     print(type(pdf))
#     # pdfkit.from_file(pdf, 'test.pdf')
    
# p = pdfkit.from_url('http://google.com', 'out.pdf')
# print(p)
# print(type(p))
# a = pdfkit.from_string(html, 'string_dd.pdf')
# with open('outme.pdf') as o:
#     r = pdfkit.from_url('http://google.com', False)
#     o.write(r)
# pdfkit.from_file('certkoto.html', 'test.pdf')

# f.close()

test = pdfkit.from_url('http://localhost:8000/cert', 'newest.pdf')
print(test)

