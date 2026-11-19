import os
import re
import traceback
from flask import Flask, render_template, request, session, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'smart-parking-esa-unggul-2026')

database_url = os.environ.get('DATABASE_URL', 'sqlite:////tmp/lokal.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app)

class DataParkir(db.Model):
    __tablename__ = 'data_parkir'
    id = db.Column(db.Integer, primary_key=True)
    plat_nomor = db.Column(db.String(20), nullable=False)
    keterangan = db.Column(db.Text, nullable=False)

class MemberParkir(db.Model):
    __tablename__ = 'member_parkir'
    id = db.Column(db.Integer, primary_key=True)
    no_hp = db.Column(db.String(25), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    plat_nomor = db.Column(db.String(20), nullable=False)

def init_db_safe():
    try:
        db.create_all()
    except Exception as e:
        print("DB Init Warning:", e)

def hitung_tarif_akhir(durasi_jam, is_member=False):
    tarif_dasar = 5000 if durasi_jam <= 1 else 5000 + (durasi_jam - 1) * 3000
    if is_member:
        diskon = int(tarif_dasar * 0.10)
        return tarif_dasar, diskon, tarif_dasar - diskon
    return tarif_dasar, 0, tarif_dasar

def render_dashboard():
    init_db_safe()
    is_member = (session.get('mode') == 'member')
    daftar_data = DataParkir.query.order_by(DataParkir.id.desc()).all()

    semua_kode_slot = [f"A{i}" for i in range(1, 21)]
    slot_terisi_map = {}

    for item in daftar_data:
        match = re.search(r'\b(A(?:[1-9]|1[0-9]|20))\b', item.keterangan.upper())
        if match:
            kode = match.group(1)
            if kode not in slot_terisi_map:
                nama_match = re.search(r'Nama:\s*([^(|]+)', item.keterangan)
                tarif_match = re.search(r'Total:\s*(Rp[\d.]+)', item.keterangan)
                bayar_match = re.search(r'(LUNAS VIA QRIS|BAYAR DI KASIR[^|]*)', item.keterangan)
                slot_terisi_map[kode] = {
                    'id': item.id,
                    'plat_nomor': item.plat_nomor,
                    'nama': nama_match.group(1).strip() if nama_match else '-',
                    'tarif': tarif_match.group(1).strip() if tarif_match else 'Rp5.000',
                    'metode': bayar_match.group(1).strip() if bayar_match else 'TERBOOKING',
                    'keterangan': item.keterangan
                }

    slots = []
    for kode in semua_kode_slot:
        if kode in slot_terisi_map:
            slots.append({
                'kode': kode,
                'status': 'TERISI',
                'id_data': slot_terisi_map[kode]['id'],
                'plat_nomor': slot_terisi_map[kode]['plat_nomor'],
                'nama': slot_terisi_map[kode]['nama'],
                'tarif': slot_terisi_map[kode]['tarif'],
                'metode': slot_terisi_map[kode]['metode'],
                'keterangan': slot_terisi_map[kode]['keterangan']
            })
        else:
            slots.append({
                'kode': kode,
                'status': 'KOSONG',
                'id_data': None,
                'plat_nomor': '-',
                'nama': '-',
                'tarif': '-',
                'metode': '-',
                'keterangan': 'Tersedia'
            })

    total_slot = len(slots)
    jumlah_terisi = len(slot_terisi_map)
    jumlah_kosong = total_slot - jumlah_terisi

    return render_template(
        'index.html',
        is_login_page=False,
        is_member=is_member,
        user=session.get('nama', 'Pengunjung'),
        no_hp=session.get('no_hp', ''),
        plat_member=session.get('plat_member', ''),
        daftar_data=daftar_data,
        slots=slots,
        total_slot=total_slot,
        jumlah_kosong=jumlah_kosong,
        jumlah_terisi=jumlah_terisi
    )

def proses_form_login():
    init_db_safe()
    aksi = request.form.get('aksi', 'member')

    if aksi == 'guest':
        session['mode'] = 'guest'
        session['nama'] = 'Pengunjung Tamu'
        session['no_hp'] = ''
        session['plat_member'] = ''
        return render_dashboard()

    no_hp = request.form.get('no_hp', '').strip()
    nama = request.form.get('nama', '').strip()
    plat = request.form.get('plat_nomor', '').strip().upper()

    if no_hp and nama and plat:
        member = MemberParkir.query.filter_by(no_hp=no_hp).first()
        if member:
            member.nama = nama
            member.plat_nomor = plat
        else:
            member = MemberParkir(no_hp=no_hp, nama=nama, plat_nomor=plat)
            db.session.add(member)
        db.session.commit()

        session['mode'] = 'member'
        session['nama'] = member.nama
        session['no_hp'] = member.no_hp
        session['plat_member'] = member.plat_nomor
        return render_dashboard()
    else:
        error = "Untuk daftar/masuk Member, wajib isi No. HP, Nama, dan Plat Kendaraan!"
        return render_template('index.html', is_login_page=True, error=error)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)
@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return proses_form_login()
    if session.get('mode'):
        return render_dashboard()
    return render_template('index.html', is_login_page=True, error=None)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('index.html', is_login_page=True, error=None)

@app.route('/keluar/<int:id>', methods=['POST'])
def kendaraan_keluar(id):
    if not session.get('mode'):
        return render_template('index.html', is_login_page=True, error=None)
    data = DataParkir.query.get_or_404(id)
    db.session.delete(data)
    db.session.commit()
    return render_dashboard()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    # Tangani tombol Ganti Akun (Logout) meskipun terkena rewrite Vercel
    if request.args.get('logout') == '1' or request.form.get('aksi') == 'logout':
        session.clear()
        return render_template('index.html', is_login_page=True, error=None)

    # Jika belum login
    if not session.get('mode'):
        if request.method == 'POST' and request.form.get('aksi'):
            return proses_form_login()
        return render_template('index.html', is_login_page=True, error=None)

    is_member = (session.get('mode') == 'member')

    if request.method == 'POST':
        init_db_safe()
        # Tangani kendaraan keluar (Gate Out)
        if request.form.get('keluar_id'):
            data = DataParkir.query.get(int(request.form.get('keluar_id')))
            if data:
                db.session.delete(data)
                db.session.commit()
            return render_dashboard()

        # Tangani booking slot baru
        nama_pengendara = request.form.get('nama_pengendara', '').strip()
        no_hp = request.form.get('no_hp', '').strip()
        plat = request.form.get('plat_nomor', '').strip().upper()
        slot_pilihan = request.form.get('slot_pilihan', '').strip()
        durasi = int(request.form.get('durasi', 1))
        metode_bayar = request.form.get('metode_bayar', 'QRIS').strip()

        if nama_pengendara and no_hp and plat and slot_pilihan:
            _, diskon, total_bayar = hitung_tarif_akhir(durasi, is_member)
            tarif_rp = f"Rp{total_bayar:,}".replace(",", ".")
            status_member = "MEMBER (Diskon 10%)" if is_member else "NON-MEMBER"
            status_bayar = "LUNAS VIA QRIS" if metode_bayar == "QRIS" else "BAYAR DI KASIR (TERVERIFIKASI)"

            ket_lengkap = (
                f"Slot {slot_pilihan} | {status_member} | Nama: {nama_pengendara} ({no_hp}) | "
                f"Durasi: {durasi} Jam | Total: {tarif_rp} | {status_bayar}"
            )
            data_baru = DataParkir(plat_nomor=plat, keterangan=ket_lengkap)
            db.session.add(data_baru)
            db.session.commit()

    return render_dashboard()

@app.errorhandler(Exception)
def handle_exception(e):
    return f"<pre>DETAIL ERROR:\n{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
