import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='../templates', static_folder='../static')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///lokal.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Struktur tabel yang akan otomatis muncul di pgAdmin kamu
class DataParkir(db.Model):
    __tablename__ = 'data_parkir'
    id = db.Column(db.Integer, primary_key=True)
    plat_nomor = db.Column(db.String(20), nullable=False)
    keterangan = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        plat = request.form.get('plat_nomor')
        ket = request.form.get('keterangan')
        if plat and ket:
            data_baru = DataParkir(plat_nomor=plat.upper(), keterangan=ket)
            db.session.add(data_baru)
            db.session.commit()
        return redirect(url_for('home'))

    daftar_data = DataParkir.query.order_by(DataParkir.id.desc()).all()
    return render_template('index.html', daftar_data=daftar_data)

if __name__ == '__main__':
    app.run(debug=True)
