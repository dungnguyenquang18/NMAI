from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, URL
import json
import requests
import tiktoken
import torch
from embeding_model.model import TransformerModel
from main_model import Chatbot
from retrive import Retriever
import re
import os
from io import BytesIO
from flask import send_file
import pdfkit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key

# JSON file setup
JSON_FILE = 'D:/3Y2S/AI/btl/NMAI/candidate_data.json'
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'w') as f:
        json.dump({}, f)  # Initialize empty dictionary

# Khởi tạo tokenizer
tokenizer = tiktoken.get_encoding('gpt2')

# Khởi tạo mô hình
vocab_size = tokenizer.n_vocab
embed_size = 512
d_model = 512
num_heads = 8
d_ff = 512
num_layers = 4
dropout = 0.1
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = TransformerModel(vocab_size, embed_size, d_model, num_heads, d_ff, num_layers, dropout)
model.load_state_dict(torch.load('D:/3Y2S/AI/btl/NMAI/best_transformer_encoder_single.pt', map_location=device))
model.to(device)
retrieve = Retriever()
llm = Chatbot()


def extract_code_block(text):
    match = re.search(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip().replace('\n', '')


def save_candidate_data(data):
    try:
        # Read existing data
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            candidate_data = json.load(f)
        
        # Update with new data (merge dictionaries)
        for key, value in data.items():
            candidate_data[key] = value
        
        # Write back to file
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(candidate_data, f, indent=4, ensure_ascii=False)
            
        return True
    except Exception as e:
        print(f"Error saving data: {str(e)}")
        return False


def load_candidate_data():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return {}


# Forms
class ContactForm(FlaskForm):
    full_name = StringField('Họ Tên Đầy Đủ', validators=[DataRequired()])
    phone = StringField('Số Điện Thoại')
    website = StringField('Trang Web Cá Nhân')
    email = StringField('Địa Chỉ Email', validators=[DataRequired(), Email()])
    linkedin = StringField('LinkedIn URL', validators=[URL()])
    submit = SubmitField('Lưu Thông Tin')


class EducationForm(FlaskForm):
    degree = StringField('Bằng Cấp', validators=[DataRequired()])
    year = StringField('Năm')
    school = StringField('Trường Học', validators=[DataRequired()])
    city = StringField('Thành Phố')
    address = StringField('Địa Chỉ Cụ Thể')
    major = StringField('Chuyên Ngành')
    submit = SubmitField('Lưu Thông Tin')


class ProfileForm(FlaskForm):
    title = StringField('Chức Danh Chuyên Môn', validators=[DataRequired()])
    experience = TextAreaField('Kinh Nghiệm, Kỹ Năng')
    strengths = TextAreaField('Điểm Mạnh')
    achievements = TextAreaField('Thành Tựu')
    submit = SubmitField('Lưu Thông Tin')


class SkillsForm(FlaskForm):
    skills = TextAreaField('Các Kĩ Năng Của Bạn', validators=[DataRequired()])
    submit = SubmitField('Lưu Thông Tin')


# API route
@app.route('/api/chatbot', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    information = retrieve.retrieve(query, tokenizer, model, k=5, device=device)

    answer = llm.answer(
        f"""Từ các mẫu CV sau:\n{information}\n hãy viết CV ở định dạng HTML bằng tiếng Việt cho tôi từ thôngoseconds tin ứng viên có cấu trúc giống JSON:\n{query} \n""")
    return jsonify(extract_code_block(answer))


# Form routes
@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    if request.method == 'POST':
        if form.validate():
            candidate_data = {
                'contact': {
                    'full_name': form.full_name.data,
                    'phone': form.phone.data,
                    'website': form.website.data,
                    'email': form.email.data,
                    'linkedin': form.linkedin.data
                }
            }
            
            try:
                if save_candidate_data(candidate_data):
                    flash('Thông tin liên hệ đã được lưu!', 'success')
                    return redirect(url_for('contact'))
                else:
                    flash('Có lỗi xảy ra khi lưu thông tin!', 'error')
            except Exception as e:
                flash(f'Lỗi: {str(e)}', 'error')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
        
    return render_template('contact.html', form=form)


@app.route('/education', methods=['GET', 'POST'])
def education():
    form = EducationForm()
    if form.validate_on_submit():
        education_data = {
            'education': {
                'degree': form.degree.data,
                'year': form.year.data,
                'school': form.school.data,
                'city': form.city.data,
                'address': form.address.data,
                'major': form.major.data
            }
        }
        save_candidate_data(education_data)
        flash('Thông tin học vấn đã được lưu!', 'success')
        return redirect(url_for('education'))
    return render_template('education.html', form=form)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = ProfileForm()
    if request.method == 'POST':
        try:
            profiles = json.loads(request.form.get('profiles', '[]'))
            
            # Save each profile
            profile_data = {
                'profiles': profiles
            }
            
            if save_candidate_data(profile_data):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True})
                flash('Thông tin hồ sơ đã được lưu!', 'success')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False})
                flash('Có lỗi xảy ra khi lưu thông tin!', 'error')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)})
            flash(f'Lỗi: {str(e)}', 'error')
            
        return redirect(url_for('profile'))
        
    return render_template('profile.html', form=form)


@app.route('/skills', methods=['GET', 'POST'])
def skills():
    form = SkillsForm()
    if form.validate_on_submit():
        skills_data = {
            'skills': {
                'skills': form.skills.data
            }
        }
        save_candidate_data(skills_data)
        flash('Thông tin kỹ năng đã được lưu!', 'success')
        return redirect(url_for('skills'))
    return render_template('skills.html', form=form)


@app.route('/preview')
def preview():
    candidate_data = load_candidate_data()
    if not candidate_data:
        flash('Không có dữ liệu để tạo CV.', 'error')
        return render_template('preview.html', cv_html=None)

    query = json.dumps(candidate_data)
    response = requests.post('http://localhost:5000/api/chatbot', json={'query': query})
    if response.status_code != 200:
        flash('Lỗi khi tạo CV từ API.', 'error')
        return render_template('preview.html', cv_html=None)

    cv_html = response.json()

    # Check if the user wants to download the CV as PDF
    if request.args.get('download') == 'pdf':
        try:
            # Convert HTML to PDF using pdfkit
            pdf = pdfkit.from_string(cv_html, False)
            # Create a BytesIO stream to hold the PDF data
            pdf_stream = BytesIO(pdf)
            pdf_stream.seek(0)
            # Send the PDF as a downloadable file
            return send_file(
                pdf_stream,
                as_attachment=True,
                download_name='cv.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            flash(f'Lỗi khi tạo PDF: {str(e)}', 'error')
            return render_template('preview.html', cv_html=cv_html)

    # Default: Render the HTML CV in the browser
    return render_template('preview.html', cv_html=cv_html)


if __name__ == '__main__':
    app.run(debug=True, port=5000)