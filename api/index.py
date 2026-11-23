import os
import re
import uuid
import traceback
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, session, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'smart-parking-esa-unggul-2026')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

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

WIB = timezone(timedelta(hours=7))

MALL_CONFIG = {
    'MALL_A': {
        'id': 'MALL_A',
        'nama': 'Mall A — Grand Central',
        'subjudul': 'Gedung Parkir 2 Lantai (Lantai 1 & Lantai 2)',
        'jumlah_lantai': 2,
        'lantai': [
            {'nama': 'Lantai 1 (Zona Utama)', 'slots': [f'A{i}' for i in range(1, 11)]},
            {'nama': 'Lantai 2 (Zona Atas)', 'slots': [f'B{i}' for i in range(1, 11)]}
        ],
        'semua_slot': [f'A{i}' for i in range(1, 11)] + [f'B{i}' for i in range(1, 11)]
    },
    'MALL_B': {
        'id': 'MALL_B',
        'nama': 'Mall B — Plaza Sentral',
        'subjudul': 'Area Parkir 1 Lantai (Wide Single-Deck)',
        'jumlah_lantai': 1,
        'lantai': [
            {'nama': 'Lantai Dasar (Single Deck)', 'slots': [f'P{i}' for i in range(1, 13)]}
        ],
        'semua_slot': [f'P{i}' for i in range(1, 13)]
    }
}

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

def get_current_owner_id():
    if session.get('mode') == 'member' and session.get('no_hp'):
        return f"MEM_{session.get('no_hp').strip()}"
    if not session.get('guest_uid'):
        session['guest_uid'] = f"GST_{uuid.uuid4().hex[:10]}"
    return session['guest_uid']

def hitung_tarif_akhir(durasi_jam, is_member=False):
    tarif_dasar = 5000 if durasi_jam <= 1 else 5000 + (durasi_jam - 1) * 3000
    if is_member:
        diskon = int(tarif_dasar * 0.10)
        return tarif_dasar, diskon, tarif_dasar - diskon
    return tarif_dasar, 0, tarif_dasar

def parse_booking_info(item, now_wib, current_owner=''):
    ket = item.keterangan
    is_dibatalkan = ('STATUS: DIBATALKAN' in ket)

    mall_match = re.search(r'Mall:\s*(MALL_[AB])', ket)
    mall_id = mall_match.group(1) if mall_match else 'MALL_A'

    slot_match = re.search(r'Slot\s+([ABP]\d+)', ket.upper())
    kode_slot = slot_match.group(1) if slot_match else None

    owner_match = re.search(r'OwnerID:\s*([^|\s]+)', ket)
    owner_id = owner_match.group(1).strip() if owner_match else ''

    nama_match = re.search(r'Nama:\s*([^(|]+)', ket)
    hp_match = re.search(r'Nama:\s*[^(]+\(([^)]+)\)', ket)
    tarif_match = re.search(r'Total:\s*(Rp[\d.]+)', ket)
    bayar_match = re.search(r'(LUNAS VIA QRIS|BAYAR DI KASIR[^|]*)', ket)
    durasi_match = re.search(r'Durasi:\s*(\d+)\s*Jam', ket)
    end_match = re.search(r'Selesai:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', ket)
    batal_time_match = re.search(r'WaktuBatal:\s*([^|]+)', ket)

    durasi_jam = int(durasi_match.group(1)) if durasi_match else 1
    waktu_habis = False
    sisa_waktu_teks = f"{durasi_jam} Jam"
    jam_selesai_teks = "-"

    if end_match:
        jam_selesai_teks = end_match.group(1).split(' ')[1] + " WIB"
        try:
            dt_end = datetime.strptime(end_match.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=WIB)
            if now_wib >= dt_end:
                waktu_habis = True
                sisa_waktu_teks = "Waktu Habis"
            else:
                diff = dt_end - now_wib
                total_menit = int(diff.total_seconds() // 60)
                jam_sisa = total_menit // 60
                menit_sisa = total_menit % 60
                sisa_waktu_teks = f"{jam_sisa}j {menit_sisa}m lagi" if jam_sisa > 0 else f"{menit_sisa}m lagi"
        except Exception:
            waktu_habis = False

    no_hp_val = hp_match.group(1).strip() if hp_match else '-'
    # Cek kepemilikan akun: cocokkan OwnerID atau No. HP member yang sedang login
    is_owner = False
    if current_owner and owner_id and current_owner == owner_id:
        is_owner = True
    elif session.get('mode') == 'member' and session.get('no_hp') and session.get('no_hp').strip() == no_hp_val:
        is_owner = True

    return {
        'id': item.id,
        'is_dibatalkan': is_dibatalkan,
        'is_owner': is_owner,
        'owner_id': owner_id,
        'mall_id': mall_id,
        'mall_nama': MALL_CONFIG[mall_id]['nama'],
        'kode_slot': kode_slot,
        'plat_nomor': item.plat_nomor,
        'nama': nama_match.group(1).strip() if nama_match else '-',
        'no_hp': no_hp_val,
        'tarif': tarif_match.group(1).strip() if tarif_match else 'Rp5.000',
        'metode': bayar_match.group(1).strip() if bayar_match else 'TERBOOKING',
        'durasi_jam': durasi_jam,
        'jam_selesai': jam_selesai_teks,
        'waktu_habis': waktu_habis,
        'sisa_waktu': sisa_waktu_teks,
        'waktu_batal': batal_time_match.group(1).strip() if batal_time_match else '-',
        'keterangan': ket
    }

def ambil_data_semua_mall(selected_mall='MALL_A'):
    init_db_safe()
    now_wib = datetime.now(WIB)
    current_owner = get_current_owner_id() if session.get('mode') in ['member', 'guest'] else ''
    daftar_raw = DataParkir.query.order_by(DataParkir.id.desc()).all()
    daftar_member = MemberParkir.query.order_by(MemberParkir.id.desc()).all()

    total_pendapatan = 0
    parsed_aktif = []
    log_pembatalan = []
    terisi_per_mall = {'MALL_A': {}, 'MALL_B': {}}

    for item in daftar_raw:
        tarif_num_match = re.search(r'Total:\s*Rp([\d.]+)', item.keterangan)
        if tarif_num_match:
            angka_str = tarif_num_match.group(1).replace('.', '')
            if angka_str.isdigit():
                total_pendapatan += int(angka_str)

        info = parse_booking_info(item, now_wib, current_owner)
        if info['is_dibatalkan']:
            log_pembatalan.append(info)
            continue

        parsed_aktif.append(info)
        m_id = info['mall_id']
        k_slot = info['kode_slot']
        if m_id in terisi_per_mall and k_slot and k_slot not in terisi_per_mall[m_id]:
            terisi_per_mall[m_id][k_slot] = info

    mall_info = MALL_CONFIG.get(selected_mall, MALL_CONFIG['MALL_A'])
    slot_map = terisi_per_mall[mall_info['id']]

    lantai_data = []
    for lt in mall_info['lantai']:
        slot_items = []
        for kode in lt['slots']:
            if kode in slot_map:
                d = slot_map[kode]
                slot_items.append({
                    'kode': kode,
                    'status': 'TERISI',
                    'id_data': d['id'],
                    'is_owner': d['is_owner'],
                    'plat_nomor': d['plat_nomor'],
                    'nama': d['nama'],
                    'tarif': d['tarif'],
                    'metode': d['metode'],
                    'jam_selesai': d['jam_selesai'],
                    'waktu_habis': d['waktu_habis'],
                    'sisa_waktu': d['sisa_waktu']
                })
            else:
                slot_items.append({
                    'kode': kode,
                    'status': 'KOSONG',
                    'id_data': None,
                    'is_owner': False,
                    'plat_nomor': '-',
                    'nama': '-',
                    'tarif': '-',
                    'metode': '-',
                    'jam_selesai': '-',
                    'waktu_habis': True,
                    'sisa_waktu': '-'
                })
        lantai_data.append({'nama': lt['nama'], 'slots': slot_items})

    total_slot = len(mall_info['semua_slot'])
    jumlah_terisi = len(slot_map)
    jumlah_kosong = total_slot - jumlah_terisi
    pendapatan_rp = f"Rp{total_pendapatan:,}".replace(",", ".")
    daftar_mall_ini = [p for p in parsed_aktif if p['mall_id'] == mall_info['id']]

    return {
        'mall_info': mall_info,
        'all_malls': MALL_CONFIG,
        'lantai_data': lantai_data,
        'daftar_data': daftar_mall_ini,
        'semua_transaksi': parsed_aktif,
        'log_pembatalan': log_pembatalan,
        'daftar_member': daftar_member,
        'total_slot': total_slot,
        'jumlah_kosong': jumlah_kosong,
        'jumlah_terisi': jumlah_terisi,
        'pendapatan_rp': pendapatan_rp
    }

def render_dashboard():
    selected_mall = session.get('selected_mall', 'MALL_A')
    ctx = ambil_data_semua_mall(selected_mall)
    mode = session.get('mode')

    if mode == 'admin':
        return render_template('index.html', page_view='admin_dashboard', **ctx)

    is_member = (mode == 'member')
    return render_template(
        'index.html',
        page_view='user_dashboard',
        is_member=is_member,
        user=session.get('nama', 'Pengunjung'),
        no_hp=session.get('no_hp', ''),
        plat_member=session.get('plat_member', ''),
        **ctx
    )

def proses_form_login():
    init_db_safe()
    aksi = request.form.get('aksi', 'member')

    if aksi == 'admin_login':
        pw = request.form.get('admin_password', '').strip()
        if pw == ADMIN_PASSWORD:
            session['mode'] = 'admin'
            session['nama'] = 'Administrator Utama'
            return render_dashboard()
        return render_template('index.html', page_view='admin_login', error="Password Admin salah! (Default: admin123)")

    if aksi == 'guest':
        session['mode'] = 'guest'
        session['nama'] = 'Pengunjung Tamu'
        session['no_hp'] = ''
        session['plat_member'] = ''
        session['guest_uid'] = f"GST_{uuid.uuid4().hex[:10]}"
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

    error = "Untuk daftar/masuk Member, wajib isi No. HP, Nama, dan Plat Kendaraan!"
    return render_template('index.html', page_view='user_login', error=error)

@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    asset = request.args.get('asset')
    if asset == 'css':
        return send_from_directory(STATIC_DIR, 'style.css', mimetype='text/css')
    if asset == 'js':
        return send_from_directory(STATIC_DIR, 'script.js', mimetype='application/javascript')

    if request.args.get('mall') in MALL_CONFIG:
        session['selected_mall'] = request.args.get('mall')

    if request.args.get('logout') == '1':
        session.clear()
        return render_template('index.html', page_view='user_login', error=None)

    if request.args.get('admin') == '1':
        if session.get('mode') == 'admin':
            return render_dashboard()
        session.clear()
        return render_template('index.html', page_view='admin_login', error=None)

    if not session.get('mode'):
        if request.method == 'POST' and request.form.get('aksi'):
            return proses_form_login()
        return render_template('index.html', page_view='user_login', error=None)

    is_member = (session.get('mode') == 'member')

    if request.method == 'POST':
        init_db_safe()
        if request.form.get('hapus_notif_id') and session.get('mode') == 'admin':
            notif_row = DataParkir.query.get(int(request.form.get('hapus_notif_id')))
            if notif_row:
                db.session.delete(notif_row)
                db.session.commit()
            return render_dashboard()

    if request.form.get('hapus_member_id') and session.get('mode') == 'admin':
            member_row = MemberParkir.query.get(int(request.form.get('hapus_member_id')))
            if member_row:
                db.session.delete(member_row)
                db.session.commit()
            return render_dashboard()

        if request.form.get('aksi') == 'hapus_semua_notif' and session.get('mode') == 'admin':
            for row in DataParkir.query.all():
                if 'STATUS: DIBATALKAN' in row.keterangan:
                    db.session.delete(row)
            db.session.commit()
            return render_dashboard()

        if request.form.get('aksi') == 'reset_semua' and session.get('mode') == 'admin':
            mall_target = session.get('selected_mall', 'MALL_A')
            for row in DataParkir.query.all():
                if 'STATUS: DIBATALKAN' not in row.keterangan:
                    if f"Mall: {mall_target}" in row.keterangan or (mall_target == 'MALL_A' and 'Mall:' not in row.keterangan):
                        db.session.delete(row)
            db.session.commit()
            return render_dashboard()

        if request.form.get('keluar_id'):
            data = DataParkir.query.get(int(request.form.get('keluar_id')))
            if data:
                # Validasi kepemilikan jika yang meminta bukan Admin
                if session.get('mode') != 'admin':
                    current_owner = get_current_owner_id()
                    info_cek = parse_booking_info(data, datetime.now(WIB), current_owner)
                    if not info_cek['is_owner']:
                        return render_dashboard()

                    jenis = request.form.get('jenis_keluar', 'selesai')
                    if jenis == 'batal':
                        waktu_batal_str = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
                        if 'STATUS: DIBATALKAN' not in data.keterangan:
                            data.keterangan = f"STATUS: DIBATALKAN | WaktuBatal: {waktu_batal_str} | {data.keterangan}"
                            db.session.commit()
                        return render_dashboard()

                    if not info_cek['waktu_habis']:
                        return render_dashboard()

                db.session.delete(data)
                db.session.commit()
            return render_dashboard()

        nama_pengendara = request.form.get('nama_pengendara', '').strip()
        no_hp = request.form.get('no_hp', '').strip()
        plat = request.form.get('plat_nomor', '').strip().upper()
        slot_pilihan = request.form.get('slot_pilihan', '').strip()
        durasi = int(request.form.get('durasi', 1))
        metode_bayar = request.form.get('metode_bayar', 'QRIS').strip()
        mall_id = session.get('selected_mall', 'MALL_A')
        owner_id = get_current_owner_id()

        if nama_pengendara and no_hp and plat and slot_pilihan:
            _, diskon, total_bayar = hitung_tarif_akhir(durasi, is_member)
            tarif_rp = f"Rp{total_bayar:,}".replace(",", ".")
            status_member = "MEMBER (Diskon 10%)" if is_member else "NON-MEMBER"
            status_bayar = "LUNAS VIA QRIS" if metode_bayar == "QRIS" else "BAYAR DI KASIR (TERVERIFIKASI)"

            now_wib = datetime.now(WIB)
            waktu_selesai = (now_wib + timedelta(hours=durasi)).strftime("%Y-%m-%d %H:%M")

            ket_lengkap = (
                f"Mall: {mall_id} | Slot {slot_pilihan} | OwnerID: {owner_id} | {status_member} | "
                f"Nama: {nama_pengendara} ({no_hp}) | Durasi: {durasi} Jam | Selesai: {waktu_selesai} | "
                f"Total: {tarif_rp} | {status_bayar}"
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
