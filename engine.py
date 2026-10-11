import json
import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from graph_data import EXERCISES

STRATEGIES = ['hint','blocks','example','retry']
KST = timezone(timedelta(hours=9))
def now(): return datetime.now(KST)
def db_path(): return os.getenv('DATABASE_PATH','learner.db')
def connection():
    con=sqlite3.connect(db_path()); con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, ts TEXT, exercise TEXT, answer TEXT, score INTEGER, correct INTEGER, diagnosis TEXT, strategy TEXT, feedback TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS policy (diagnosis TEXT, strategy TEXT, weight REAL, PRIMARY KEY(diagnosis,strategy))')
    con.execute('CREATE TABLE IF NOT EXISTS mastery (topic TEXT PRIMARY KEY, value REAL, due TEXT)')
    con.commit(); return con

def choose_strategy(diagnosis):
    con=connection()
    rows=con.execute('SELECT strategy,weight FROM policy WHERE diagnosis=?',(diagnosis,)).fetchall()
    con.close()
    weights={r['strategy']:r['weight'] for r in rows}
    return random.choices(STRATEGIES,weights=[weights.get(s,1.0) for s in STRATEGIES],k=1)[0]

def save_attempt(exercise,answer,result,strategy):
    con=connection(); score=result['score']; correct=result['correct']; diagnosis=result['diagnosis_id']
    con.execute('INSERT INTO attempts(ts,exercise,answer,score,correct,diagnosis,strategy,feedback) VALUES (?,?,?,?,?,?,?,?)',
                (now().isoformat(),exercise['id'],answer,score,int(correct),diagnosis,strategy,result['explanation_id']))
    old=con.execute('SELECT value FROM mastery WHERE topic=?',(exercise['topic'],)).fetchone()
    value=float(old['value']) if old else 0.2
    value=max(0.0,min(1.0, value*0.75+(score/100)*0.25))
    days=1 if value<0.5 else (3 if value<0.8 else 7)
    con.execute('INSERT INTO mastery(topic,value,due) VALUES(?,?,?) ON CONFLICT(topic) DO UPDATE SET value=excluded.value,due=excluded.due',
                (exercise['topic'],value,(now()+timedelta(days=days)).isoformat()))
    # Proxy reward only: observed correctness, not validated teaching effectiveness.
    reward=1 if correct else 0
    row=con.execute('SELECT weight FROM policy WHERE diagnosis=? AND strategy=?',(diagnosis,strategy)).fetchone()
    weight=float(row['weight']) if row else 1.0
    weight=max(0.2,min(4.0,weight+(0.12 if reward else -0.04)))
    con.execute('INSERT INTO policy(diagnosis,strategy,weight) VALUES(?,?,?) ON CONFLICT(diagnosis,strategy) DO UPDATE SET weight=excluded.weight',(diagnosis,strategy,weight))
    con.commit();con.close()
    return value

def history():
    con=connection(); rows=con.execute('SELECT * FROM attempts ORDER BY id DESC LIMIT 40').fetchall(); con.close();return [dict(r) for r in rows]
def mastery():
    con=connection();rows=con.execute('SELECT * FROM mastery').fetchall();con.close();return {r['topic']:dict(r) for r in rows}
def policy_rows():
    con=connection();rows=con.execute('SELECT * FROM policy ORDER BY diagnosis,strategy').fetchall();con.close();return [dict(r) for r in rows]

def demo_evaluate(exercise,answer):
    normalized=lambda x: ''.join(x.strip().replace('.','').split())
    correct=normalized(answer)==normalized(exercise['reference'])
    return {'correct':correct,'score':100 if correct else 30,'reference':exercise['reference'],
            'diagnosis_id':'none' if correct else 'expression',
            'explanation_id':'Cocok dengan contoh jawaban.' if correct else 'Mode demo: hanya memeriksa kecocokan dengan satu contoh, bukan menilai semua jawaban benar.',
            'hint_id':'Perhatikan susunan kalimat, partikel, dan bentuk kata kerja.', 'suggested_words':[]}
