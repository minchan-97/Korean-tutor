NODES = {
 '먹다': ('makan','kata kerja'), '밥': ('nasi / makanan','kata benda'), '마시다': ('minum','kata kerja'),
 '물': ('air','kata benda'), '학교': ('sekolah','tempat'), '가다': ('pergi','kata kerja'),
 '공부하다': ('belajar','kata kerja'), '어제': ('kemarin','waktu'), '오늘': ('hari ini','waktu'),
 '친구': ('teman','kata benda'), '만나다': ('bertemu','kata kerja'), '먹었어요': ('sudah makan','bentuk lampau'),
 '갔어요': ('sudah pergi','bentuk lampau'), '먹어요': ('makan','bentuk sopan'), '가요': ('pergi','bentuk sopan'),
 '식사하다': ('bersantap','sinonim'), '드시다': ('makan (hormat)','honorifik'),
 '을/를': ('penanda objek','partikel'), '에': ('ke / di','partikel'), '에서': ('di (tempat aktivitas)','partikel')
}
EDGES = [
 ('먹다','밥','objek'),('먹다','마시다','berkaitan'),('마시다','물','objek'),
 ('먹다','먹어요','konjugasi'),('먹다','먹었어요','lampau'),('먹다','식사하다','sinonim'),
 ('먹다','드시다','honorifik'),('먹다','을/를','pola tata bahasa'),
 ('가다','학교','tujuan'),('가다','가요','konjugasi'),('가다','갔어요','lampau'),
 ('학교','에','partikel tujuan'),('학교','에서','partikel kegiatan'),('학교','공부하다','aktivitas'),
 ('어제','갔어요','waktu lampau'),('어제','먹었어요','waktu lampau'),
 ('친구','만나다','objek'),('오늘','가요','waktu kini')]
EXERCISES = [
 {'id':'ex1','level':'A1','topic':'먹다','instruction':'Tulis dalam bahasa Korea: Saya makan nasi. (gaya sopan)', 'reference':'저는 밥을 먹어요.', 'blocks':['저는','밥을','먹어요','먹었어요','학교에'], 'targets':['저는','밥을','먹어요']},
 {'id':'ex2','level':'A1','topic':'가다','instruction':'Tulis dalam bahasa Korea: Kemarin saya pergi ke sekolah.', 'reference':'저는 어제 학교에 갔어요.', 'blocks':['저는','어제','학교에','갔어요','가요'], 'targets':['저는','어제','학교에','갔어요']},
 {'id':'ex3','level':'A1','topic':'먹다','instruction':'Tulis dalam bahasa Korea: Kemarin saya makan nasi.', 'reference':'저는 어제 밥을 먹었어요.', 'blocks':['저는','어제','밥을','먹었어요','먹어요'], 'targets':['저는','어제','밥을','먹었어요']},
 {'id':'ex4','level':'A1','topic':'학교','instruction':'Tulis dalam bahasa Korea: Saya belajar di sekolah.', 'reference':'저는 학교에서 공부해요.', 'blocks':['저는','학교에서','학교에','공부해요','가요'], 'targets':['저는','학교에서','공부해요']},
 {'id':'ex5','level':'A2','topic':'만나다','instruction':'Tulis dalam bahasa Korea: Kemarin saya bertemu teman.', 'reference':'저는 어제 친구를 만났어요.', 'blocks':['저는','어제','친구를','만났어요','만나요'], 'targets':['저는','어제','친구를','만났어요']}
]
