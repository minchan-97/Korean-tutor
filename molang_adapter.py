"""Real Molang ThoughtStructure NM and Markov magnet-word adapter.
No untrusted legacy pickle is loaded; this learner starts with an isolated state.
"""
import json, sqlite3
from pathlib import Path
from molang_core.thought_structure import ThoughtStructure, JudgmentNode
from molang_core import markov_mass, semantic_map, word_gravity
from engine import connection

STRATEGIES={"hint":"Petunjuk bertahap", "blocks":"Blok kata", "example":"Contoh tambahan", "retry":"Coba lagi"}

def _schema(con):
    con.execute("CREATE TABLE IF NOT EXISTS nm_state (id INTEGER PRIMARY KEY CHECK(id=1), transitions TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS nm_audit (id INTEGER PRIMARY KEY, exercise TEXT, diagnosis TEXT, path TEXT, probabilities TEXT, feedback REAL, created TEXT DEFAULT CURRENT_TIMESTAMP)")
    con.execute("CREATE TABLE IF NOT EXISTS word_docs (id INTEGER PRIMARY KEY, text TEXT NOT NULL, source TEXT NOT NULL, approved INTEGER NOT NULL DEFAULT 0)")
    con.commit()

def new_tree():
    t=ThoughtStructure(learning_rate=0.1,continuity=0.8)
    t.add_node(JudgmentNode('root','Pilih strategi pengajaran'),is_root=True)
    for d in ['tense','particle','word_order','vocabulary','expression','none']:
        t.add_node(JudgmentNode(d,'Kesulitan: '+d))
        t.add_branch('root',d,1.0)
        for s in STRATEGIES:
            leaf=f'{d}:{s}'
            t.add_node(JudgmentNode(leaf,STRATEGIES[s],directive=s,is_terminal=True))
            t.add_branch(d,leaf,1.0)
    return t

def _load(con):
    t=new_tree()
    row=con.execute('SELECT transitions FROM nm_state WHERE id=1').fetchone()
    if row:
        saved=json.loads(row[0])
        for frm,targets in saved.items():
            if frm in t.transitions:
                for to,p in targets.items():
                    if to in t.transitions[frm]: t.transitions[frm][to]=float(p)
                t._normalize(frm)
    return t

def choose(diagnosis,exercise_id):
    if diagnosis not in ['tense','particle','word_order','vocabulary','expression','none']: diagnosis='expression'
    con=connection();_schema(con);t=_load(con)
    def chooser(node,candidates,candidate_nodes,probs,context):
        if node.id=='root': return diagnosis
        # weighted NM path, not an LLM-made post-hoc explanation
        import random
        return random.choices(candidates,weights=probs,k=1)[0]
    rec=t.traverse(choose_fn=chooser,context=f'{exercise_id}:{diagnosis}')
    con.close()
    return rec.path[-1].split(':')[-1],rec

def update(exercise_id,diagnosis,rec,feedback):
    con=connection();_schema(con);t=_load(con)
    t.learn(rec,max(-1.,min(1.,float(feedback))))
    con.execute('INSERT INTO nm_state(id,transitions) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET transitions=excluded.transitions',(json.dumps(t.transitions,ensure_ascii=False),))
    con.execute('INSERT INTO nm_audit(exercise,diagnosis,path,probabilities,feedback) VALUES(?,?,?,?,?)',(exercise_id,diagnosis,json.dumps(rec.path,ensure_ascii=False),json.dumps(rec.at_probs,ensure_ascii=False),feedback))
    con.commit();con.close()

def policy():
    con=connection();_schema(con);t=_load(con);con.close()
    return [{'diagnosis':d,'strategy':s,'probability':round(t.transitions[d][f'{d}:{s}'],4)} for d in ['tense','particle','word_order','vocabulary','expression','none'] for s in STRATEGIES]

def audit():
    con=connection();_schema(con);rows=con.execute('SELECT * FROM nm_audit ORDER BY id DESC LIMIT 30').fetchall();con.close()
    return [dict(r) for r in rows]

def add_document(text,source='learner',approved=False):
    text=text.strip()[:500]
    if not text: return
    con=connection();_schema(con)
    con.execute('INSERT INTO word_docs(text,source,approved) VALUES(?,?,?)',(text,source,int(approved)))
    con.commit();con.close()

def magnet_neighbors(word):
    con=connection();_schema(con)
    docs=[dict(r) for r in con.execute('SELECT text,source FROM word_docs WHERE approved=1 ORDER BY id DESC LIMIT 500')]
    con.close()
    if not docs:return [],{}
    mk=markov_mass.count(docs)
    nxt=markov_mass.next_of(mk,word,k=8)
    return nxt,markov_mass.masses(mk)
