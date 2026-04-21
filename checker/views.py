from django.shortcuts import render
from django.http import HttpResponse
from difflib import SequenceMatcher, unified_diff
from reportlab.pdfgen import canvas
import datetime


ALLOWED_EXTENSIONS = ['.py', '.java', '.cpp', '.c', '.txt']
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB


def is_valid_file(file):
    if not file:
        return False

    if file.size > MAX_FILE_SIZE:
        return False

    filename = file.name.lower()
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def clean_code(code):
    lines = code.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#") or line.startswith("//"):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)

def generate_pdf(request, similarity):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="plagiarism_report.pdf"'

    p = canvas.Canvas(response)

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(150, 800, "Plagiarism Checker Report")

    # Similarity
    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Similarity Score: {similarity}%")

    # Status
    if similarity > 80:
        status = "HIGH PLAGIARISM"
    elif similarity > 50:
        status = "MEDIUM SIMILARITY"
    else:
        status = "LOW SIMILARITY"

    p.drawString(100, 740, f"Status: {status}")

    # Date
    p.drawString(100, 720, f"Generated On: {datetime.datetime.now()}")

    p.showPage()
    p.save()

    return response


def upload_files(request):
    if request.method == 'POST':
        file1 = request.FILES.get('file1')
        file2 = request.FILES.get('file2')

        
        if not file1 or not file2:
            return render(request, 'upload.html', {
                'message': 'Please upload both files!'
            })

        
        if not is_valid_file(file1) or not is_valid_file(file2):
            return render(request, 'upload.html', {
                'message': 'Invalid file or file exceeds 15MB limit!'
            })

        
        try:
            code1 = file1.read().decode('utf-8', errors='ignore')
            code2 = file2.read().decode('utf-8', errors='ignore')
        except Exception:
            return render(request, 'upload.html', {
                'message': 'Error reading files!'
            })

        # Empty check
        if not code1.strip() or not code2.strip():
            return render(request, 'upload.html', {
                'message': 'Files cannot be empty!'
            })

        # Clean code
        code1_clean = clean_code(code1)
        code2_clean = clean_code(code2)

        similarity = SequenceMatcher(None, code1_clean, code2_clean).ratio() * 100
        similarity = round(similarity, 2)

        width = f"{similarity}%"

        
        if similarity > 80:
            bar_class = "high-bar"
        elif similarity > 50:
            bar_class = "medium-bar"
        else:
            bar_class = "low-bar"

        # Diff
        diff = list(unified_diff(
            code1_clean.splitlines(),
            code2_clean.splitlines(),
            lineterm=''
        ))

        formatted_diff = []
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                formatted_diff.append(('add', line))
            elif line.startswith('-') and not line.startswith('---'):
                formatted_diff.append(('remove', line))
            else:
                formatted_diff.append(('normal', line))

        # Return result
        return render(request, 'result.html', {
            'similarity': similarity,
            'diff': formatted_diff,
            'width': width,
            'bar_class': bar_class,
            'pdf_similarity': int(similarity)
        })

    return render(request, 'upload.html')