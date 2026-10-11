import os
import hmac
import streamlit as st
from graph_data import NODES, EDGES, EXERCISES
from engine import connection, save_attempt, history, mastery, demo_evaluate
from molang_adapter import choose, update, policy, audit, add_document, magnet_neighbors
from llm_client import configured, evaluate
from dynamic_magnet import build as build_dynamic, explore as explore_dynamic, propose as propose_words, candidates as word_candidates, review as review_word

st.set_page_config(page_title='Korean Magnet Tutor',page_icon='🇰🇷',layout='wide')

def setting(name):
    try: return st.secrets.get(name,os.getenv(name,''))
    except Exception: return os.getenv(name,'')

password=setting('APP_PASSWORD')
if password:
    if not st.session_state.get('authorized'):
        st.title('🔐 Korean Magnet Tutor')
        entered=st.text_input('Kata sandi / 비밀번호',type='password')
        if st.button('Masuk',type='primary'):
            if hmac.compare_digest(entered,password): st.session_state.authorized=True;st.rerun()
            else: st.error('Kata sandi salah.')
        st.stop()

connection().close()
st.title('🇮🇩 → 🇰🇷 Korean Magnet Tutor')
st.caption('Belajar bahasa Korea dengan peta kosakata, blok kata, dan umpan balik adaptif')
if not configured():
    st.warning('Mode demo: belum ada OPENAI_API_KEY. Penilaian hanya mencocokkan contoh jawaban dan tidak memahami variasi yang benar.')
else:
    st.success('AI tutor aktif. Koreksi AI tetap dapat salah; gunakan sebagai bantuan belajar.')

study,magnet,graph,progress=st.tabs(['✍️ Latihan menulis','🧲 Blok kata','🕸️ Peta kosakata','📈 Kemajuan'])
with study:
    st.subheader('Latihan menulis bahasa Korea')
    ex=st.selectbox('Pilih latihan',EXERCISES,format_func=lambda e:f"{e['level']} · {e['instruction']}",key='exercise_choice')
    st.info(ex['instruction'])
    answer=st.text_area('Jawaban Anda dalam bahasa Korea',key=f"answer_{ex['id']}",height=100,placeholder='Tulis kalimat bahasa Korea...')
    if st.button('Periksa jawaban',type='primary',disabled=not answer.strip()):
        try:
            result=evaluate(ex,answer.strip()) if configured() else demo_evaluate(ex,answer.strip())
            strategy,record=choose(result['diagnosis_id'],ex['id'])
            value=save_attempt(ex,answer.strip(),result,strategy)
            # Do not train on the answer that preceded the teaching action.
            # NM feedback is collected after a subsequent attempt below.
            st.session_state['pending_nm']=(ex['id'],result['diagnosis_id'],record)
            add_document(answer.strip(),source='learner',approved=False)
            propose_words(result.get('suggested_words',[]),source='llm')
            st.session_state['latest']=(ex['id'],result,strategy,value)
        except Exception as err:
            st.error('Gagal menghubungi model atau menyimpan hasil. Periksa koneksi, model, dan secrets.')
    latest=st.session_state.get('latest')
    if latest and latest[0]==ex['id']:
        _,r,strategy,value=latest
        st.metric('Skor perkiraan',f"{r['score']}/100")
        st.write('**Contoh jawaban:**',r['reference'])
        st.write('**Umpan balik:**',r['explanation_id'])
        st.write('**Petunjuk:**',r['hint_id'])
        labels={'hint':'petunjuk bertahap','blocks':'susun blok kata','example':'lihat contoh tambahan','retry':'coba jawab lagi'}
        st.write('**Strategi NM berikutnya:**',labels[strategy])
        st.caption(f"Estimasi penguasaan topik '{ex['topic']}': {value:.0%} (heuristik, bukan hasil tes baku)")
        if strategy=='blocks': st.info('Buka tab 🧲 Blok kata untuk latihan menyusun kalimat.')
        st.caption('NM: keputusan berasal dari ThoughtStructure asli. Nilai efektivitas strategi belum teruji.')
        with st.expander('Jejak keputusan NM'):
            pending=st.session_state.get('pending_nm')
            if pending and pending[0]==ex['id']:
                st.json({'path':pending[2].path,'probabilities_at_choice':pending[2].at_probs})
        st.write('**Setelah mencoba strategi ini, apakah latihan lanjutan membantu?**')
        left,right=st.columns(2)
        with left:
            if st.button('Ya, berhasil',key='nm_yes'):
                pending=st.session_state.pop('pending_nm',None)
                if pending: update(*pending,feedback=1.0);st.success('NM diperbarui berdasarkan umpan balik eksplisit.')
        with right:
            if st.button('Belum berhasil',key='nm_no'):
                pending=st.session_state.pop('pending_nm',None)
                if pending: update(*pending,feedback=-1.0);st.info('NM diperbarui berdasarkan umpan balik eksplisit.')
        if r['suggested_words']:
            st.write('**Usulan kosakata dari AI (belum diverifikasi):**')
            for word in r['suggested_words']: st.write(f"• {word['korean']} — {word['indonesian']}")

with magnet:
    st.subheader('Susun kalimat dengan blok kata')
    exm=st.selectbox('Pilih kalimat',EXERCISES,format_func=lambda e:e['instruction'],key='magnet_exercise')
    st.write(exm['instruction'])
    state_key='blocks_'+exm['id']
    if state_key not in st.session_state: st.session_state[state_key]=[]
    chosen=st.session_state[state_key]
    st.write('**Kalimat Anda:**', ' '.join(chosen) if chosen else '—')
    for i,word in enumerate(chosen):
        if st.button('✕ '+word,key=f'rm_{exm["id"]}_{i}'):
            chosen.pop(i);st.rerun()
    st.write('**Pilih blok:**')
    cols=st.columns(3)
    for i,word in enumerate(exm['blocks']):
        with cols[i%3]:
            if st.button('＋ '+word,key=f'add_{exm["id"]}_{i}',disabled=word in chosen):
                chosen.append(word);st.rerun()
    c1,c2=st.columns(2)
    with c1:
        if st.button('Ulangi',key='reset_blocks'): st.session_state[state_key]=[];st.rerun()
    with c2:
        if st.button('Periksa susunan',key='check_blocks'):
            if chosen==exm['targets']: st.success('Bagus! Cocok dengan contoh susunan.')
            else: st.info('Belum cocok dengan contoh susunan. Cek urutan dan bentuk kata kerja.')
    st.caption('Latihan blok hanya mencocokkan satu susunan contoh; jawaban alternatif dapat benar.')

with graph:
    st.caption('Hubungan linguistik terkurasi dan magnet Markov asli disajikan terpisah; kemunculan bersama bukan bukti hubungan gramatikal.')
    st.subheader('Peta hubungan kosakata')
    center=st.selectbox('Kata pusat',list(NODES),index=0)
    related=[]
    for a,b,relation in EDGES:
        if a==center: related.append((b,relation))
        elif b==center: related.append((a,relation))
    st.markdown(f"### {center} — {NODES[center][0]}")
    if related:
        st.write('**Hubungan kosakata:**')
        for word,relation in related:
            st.write(f"🔗 **{word}** — {NODES[word][0]} · _{relation}_")
    else: st.write('Belum ada hubungan tersimpan untuk kata ini.')
    st.caption('Peta awal terkurasi. Saran AI tidak masuk otomatis.')
    st.divider()
    st.subheader('Magnet kata Molang (Markov asli)')
    st.caption('Hanya dokumen yang disetujui dipakai sebagai korpus; data pribadi tidak otomatis disebar.')
    corpus=st.text_area('Tambahkan contoh kalimat bahasa Korea yang sudah diperiksa',key='corpus_input')
    if st.button('Setujui dan simpan contoh',disabled=not corpus.strip()):
        add_document(corpus,source='teacher',approved=True);st.success('Tersimpan')
    neighbors,masses=magnet_neighbors(center)
    st.write('Urutan kata terkait berdasarkan korpus disetujui:',neighbors or 'Belum cukup contoh berulang')
    st.caption('Markov asli menghitung urutan kemunculan, bukan kebenaran bahasa.')

    st.divider()
    st.subheader('🌱 Peta dinamis Molang: Semantic Map + Word Gravity + Markov')
    st.caption('Peta ini dibangun ulang dari kalimat yang disetujui. Ko-kemunculan, tarikan, dan urutan bukan bukti bahwa kata merupakan sinonim atau pasangan tata bahasa yang benar.')
    if st.button('Bangun / segarkan peta',key='refresh_dynamic'):
        st.session_state['dynamic_state']=build_dynamic()
    state=st.session_state.get('dynamic_state')
    if state is None:
        state=build_dynamic();st.session_state['dynamic_state']=state
    st.write(f"Dokumen disetujui: {state['docs']} · simpul: {len(state['map']['freq'])} · hubungan: {len(state['map']['edges'])} · klaster: {len(state['clusters'])}")
    vocab=sorted(state['map']['freq'])
    if vocab:
        selected=st.selectbox('Jelajahi simpul yang teramati',vocab,key='dynamic_center')
        detail=explore_dynamic(selected,state)
        c1,c2=st.columns(2)
        with c1:
            st.write('**Kata yang muncul bersama**');st.dataframe([{'kata':a,'bobot':b} for a,b in detail['cooccurrence']],hide_index=True)
            st.write('**Urutan Markov berikutnya**');st.write(detail['sequences'])
        with c2:
            st.write('**Tarikan Word Gravity**');st.dataframe([{'kata':a,'tarikan':b} for a,b in detail['gravity']],hide_index=True)
            st.write('**Cabang yang diperkirakan**');st.json(detail['branch'])
        st.write('**Kelompok semantik (berdasarkan ko-kemunculan)**')
        st.dataframe([{'nama':c['name'],'anggota':', '.join(c['members']),'ukuran':c['size']} for c in state['clusters'][:15]],hide_index=True)
    else:
        st.info('Belum ada hubungan yang cukup kuat. Tambahkan beberapa kalimat yang telah diperiksa, dengan kosakata yang berulang, lalu segarkan peta.')
    st.divider()
    st.subheader('🛡️ Tinjau usulan kosakata AI')
    st.caption('Kandidat dari LLM tidak otomatis menjadi fakta atau materi pelajaran. Periksa arti dan penggunaannya secara manual.')
    pending=word_candidates()
    if not pending:st.info('Tidak ada kandidat menunggu persetujuan.')
    for item in pending[:30]:
        left,right,third=st.columns([5,1,1])
        left.write(f"**{item['korean']}** — {item['indonesian']}")
        if right.button('✓',key=f"approve_{item['id']}",help='Setujui sebagai pasangan kosakata'):
            review_word(item['id'],True);st.rerun()
        if third.button('✕',key=f"reject_{item['id']}",help='Tolak kandidat'):
            review_word(item['id'],False);st.rerun()
    st.caption('Persetujuan kosakata menyimpan pasangan terjemahan; hanya kalimat contoh yang disetujui masuk ke peta ko-kemunculan.')


with progress:
    st.subheader('Riwayat belajar (satu pengguna)')
    records=history(); levels=mastery()
    if records:
        st.metric('Jumlah latihan',len(records))
        st.dataframe([{'Waktu':r['ts'][:16],'Latihan':r['exercise'],'Skor':r['score'],'Diagnosis':r['diagnosis'],'Strategi':r['strategy']} for r in records],use_container_width=True,hide_index=True)
    else: st.info('Belum ada latihan.')
    if levels:
        st.write('**Estimasi penguasaan & jadwal ulasan:**')
        st.dataframe([{'Topik':k,'Penguasaan':f"{v['value']:.0%}",'Ulas kembali':v['due'][:10]} for k,v in levels.items()],hide_index=True,use_container_width=True)
    with st.expander('Transparansi strategi NM'):
        st.write('Bobot strategi yang disimpan (bukan bukti efektivitas pedagogis):')
        st.dataframe(policy(),hide_index=True,use_container_width=True)
    st.caption('Data disimpan dalam SQLite lokal di server. Jika hosting tidak memiliki penyimpanan permanen, riwayat dapat hilang setelah restart.')

st.divider()
st.caption('Prototipe untuk satu pelajar · Hindari memasukkan informasi pribadi atau sensitif dalam jawaban.')

with st.expander('Audit NM asli (terbaru)'):
    st.dataframe(audit(),use_container_width=True)
