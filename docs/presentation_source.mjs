import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile,registerPdfFontFace} from '@oai/artifact-tool';
const home=process.env.USERPROFILE;
const project=path.join(home,'Desktop','Projekt_ceny_mieszkan');
const workspace=process.cwd();
const tmp=path.join(workspace,'work','price_deck');
const out=path.join(workspace,'outputs','price_project');
await fs.mkdir(out,{recursive:true});
const runtime=path.join(home,'.cache','codex-runtimes','codex-primary-runtime','dependencies');
const skill=path.join(home,'.codex','plugins','cache','openai-primary-runtime','presentations','26.1112.11217','skills','presentations');
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(project,'docs/presentation_data.json'),'utf8'));
for(const [weight,file]of [[400,'arial.ttf'],[700,'arialbd.ttf']])registerPdfFontFace({family:'Arial',weight,style:'normal',source:new Uint8Array(await fs.readFile(path.join(process.env.WINDIR,'Fonts',file)))});
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#15334C',muted:'#536C80',blue:'#1674A5',teal:'#168D8A',orange:'#D87C3D',bg:'#F7FAFC',white:'#FFFFFF'};
function text(slide,s,x,y,w,h,size=27,bold=false,color=C.ink){
 const sh=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=s;sh.text.style={fontFamily:'Arial',fontSize:size,bold,color};return sh;
}
function slide(title,subtitle,notes){
 const s=deck.slides.add();s.background.fill=C.bg;
 text(s,'DATA SCIENCE  /  PROJEKT ZALICZENIOWY',64,34,1150,24,16,true,C.muted);
 text(s,title,64,86,1150,104,40,true);
 if(subtitle)text(s,subtitle,64,190,1150,62,23,false,C.muted);
 text(s,'Ceny mieszkań • publiczne dane • wydanie 15.11.2026',64,675,1050,22,15,false,C.muted);
 text(s,String(deck.slides.items.length).padStart(2,'0')+' / 13',1130,675,100,22,15,true,C.muted);
 s.speakerNotes.text=notes;return s;
}
function bullets(s,items,y=275,size=28){items.forEach((a,i)=>text(s,a,76,y+i*105,1110,90,size));}
function chart(s,type,categories,series,opts={}){
 series=series.map(r=>({...r,values:r.values.map(v=>v===null?null:Number(v.toFixed(2)))}));
 const ch=s.charts.add(type,{position:{left:76,top:265,width:1110,height:350},categories,series,hasLegend:series.length>1,legend:{position:'bottom'},chartFill:C.bg,plotAreaFill:C.bg,xAxis:{textStyle:{fontFamily:'Arial',fontSize:16,color:C.muted}},yAxis:{textStyle:{fontFamily:'Arial',fontSize:16,color:C.muted},numberFormatCode:'0.0',majorGridlines:{fill:'#D6E2EB',width:1}},dataLabels:{showValue:type==='bar',position:'outEnd',textStyle:{fontFamily:'Arial',fontSize:18,color:C.ink}},...opts});
 applyPresentationChartFont(ch,{fontFamily:'Arial'});return ch;
}
let s=slide('Czy potrafimy prognozować\nceny mieszkań?', 'Model średnich cen transakcyjnych w polskich miastach',
'40 s. Przedstaw pytanie: czy model daje przewagę nad prostymi regułami? Projekt wyodrębnia prognozę cen z szerszych badań. To średnie miejskie PLN/m², nie wycena mieszkania. Źródła: NBP BaRN, GUS, BIS, NBP MIR/SLOOS, AMRON-SARFiN; docs/SOURCES.md.');
text(s,'17 miast   ×   2 rynki   ×   5 punktów ścieżki',76,300,1120,70,36,true,C.blue);
text(s,'Lepszy wynik historyczny.\nBrak stabilnej przewagi w ostatnim okresie.',76,425,1100,140,36,true);
s=slide('Co dokładnie przewidujemy?','Średnia cena transakcyjna PLN/m², osobno dla rynku pierwotnego i wtórnego',
'35 s. q to umowny kwartał odniesienia. Model zwraca Pq do Pq+4, a h0 jest nowcastem, bo znana cena ma opóźnienie. Nie znamy parametrów pojedynczych mieszkań ani czasu sprzedaży. Zakres bez alarmów sprzedaży i płynności. Źródło: docs/DATA_DICTIONARY.md.');
bullets(s,['Ścieżka q…q+4 względem ostatniej opublikowanej ceny.','Cechy lokalne, makroekonomiczne i kredytowe.','Zastosowanie: porównanie scenariuszy miejskich i błędów modelu.']);
s=slide('Publiczne źródła i jawna jednostka danych','Oryginalne pliki, hashe SHA256, kontrola duplikatów i braków',
'50 s. NBP to ceny, GUS płace, BIS CPI i stopy, MIR/SLOOS kredyt, AMRON liczby kredytów. 11895 etykiet to 2379 wektorów razy5, nie niezależne cykle. Raw ma9337 odczytów cen/ofert/indeksów. Licencje i pobieranie opisane osobno. Źródła: data/raw/source_manifest.json; reports/tables/dataset_audit.json; https://stat.gov.pl/copyright/ ; https://data.bis.org/help/legal ; https://nbp.pl/publikacje/cykliczne-materialy-analityczne-nbp/rynek-nieruchomosci/informacja-kwartalna/ .');
bullets(s,['NBP BaRN / MIR / SLOOS • GUS • BIS • AMRON-SARFiN','Ceny 2006Q3–2026Q2; 9 337 odczytów cen, ofert i indeksów.','11 895 etykiet horyzontów = 2 379 grup miasto–rynek–kwartał.']);
s=slide('EDA: trend i struktura rynku','Warszawa, ceny transakcyjne NBP; punkty roczne z II kwartału',
'45 s. Poziomy cen są silnie trendowe. Pierwotny i wtórny nie mają identycznych poziomów/dynamiki. Między okresami widoczne są wzrosty i wyhamowania. Średnia zależy od miksu sprzedawanych mieszkań; korelacja nie dowodzi przyczynowości. Dane: data/processed/prices_long.csv, NBP BaRN.');
const cats=[...new Set(data.warsaw_history.map(r=>r.quarter))].sort();
chart(s,'line',cats.map(q=>q.slice(0,4)),['primary','secondary'].map((m,i)=>({name:m==='primary'?'Pierwotny':'Wtórny',values:cats.map(q=>data.warsaw_history.find(r=>r.quarter===q&&r.market===m)?.value??null),fill:i?C.teal:C.blue})),{yAxis:{numberFormatCode:'#,##0',textStyle:{fontFamily:'Arial',fontSize:16}}});
s=slide('24 cechy liczbowe + miasto i rynek','Braki strukturalne pozostają NaN do treningu; etykiety cen nie są imputowane',
'45 s. Trzy bloki: dynamika lokalna; makro i kredyt; relacje rynkowe/hedoniczne. Ceny ofertowe nie są etykietą. Nie interpolujemy brakujących celów. Wszystkie definicje i jednostki w docs/DATA_DICTIONARY.md. Nie korzystamy z komercyjnych statusów rezerwacji.');
bullets(s,['Ceny: dynamika, przyspieszenie, zmienność i relacje między miastami.','Makro: inflacja, stopy, płace, oprocentowanie i popyt na kredyt.','Kredyty i rynek: liczby kredytów, udział spadków, indeksy hedoniczne.'],275,27);
s=slide('Podział czasowy chroni przed przyszłością','Cały kwartał odniesienia — wszystkie miasta, rynki i horyzonty — w jednym foldzie',
'55 s. Znana cena ma lag2, czasem1 z kalendarza. Makro lag1, liczby kredytów lag2. Do uczenia wpuszczamy całe ścieżki, gdy origin+6 jest ściśle przed origin prognozy. Mediana, wskaźniki braków, skalowanie i OneHot są w Pipeline fitowanym na treningu. Uczciwie: źródła są rewizjami, nie wszystkimi prawdziwymi vintages. Historia już była analizowana; brak dziewiczego testu prospektywnego. Źródło: src/features.py; src/train.py; models/protocol.json.');
bullets(s,['Ceny: q−2 / warunkowo q−1; makro: q−1; liczby kredytów: q−2.','Ścieżka etykiet dojrzewa w origin+6 i musi poprzedzać decyzję.','Imputacja, skalowanie i kodowanie kategorii wyłącznie na train.'],275,27);
s=slide('Trzy algorytmy, siedem konfiguracji','6 foldów czasowych; wybór według MAPE h4 na walidacji',
'45 s. RF, Ridge, HGB;42próby. Wszystkie zapisane, bez selekcji na końcowej dacie. Wygrywa RF120 depth6 minleaf12 i12dojrzałych kwartałów. Parametry są config/config.yaml, wyniki reports/tables/tuning_all_trials.csv i tuning_summary.csv. Różnica między RF wariantami jest mała.');
const tuneNames={rf_12_d6:'RF:12kw.,d6',rf_12_d4:'RF:12kw.,d4',hgb_12_l7:'HGB:12kw.',hgb_20_l7:'HGB:20kw.',rf_20_d4:'RF:20kw.,d4',ridge_20_a1000:'Ridge:20kw.',ridge_12_a100:'Ridge:12kw.'};
chart(s,'bar',data.tuning.map(r=>tuneNames[r.trial]),[{name:'MAPE (%)',values:data.tuning.map(r=>Number(r.MAPE_h4.toFixed(2))),fill:C.blue}],{barOptions:{direction:'column'},yAxis:{minimumScale:0,numberFormatCode:'0.0'}});
s=slide('Historia: RF poprawia punkt odniesienia','2015Q1–2025Q1 • 41 dat • 1 394 grupy • koniec ścieżki h4',
'45 s. RF5.55,mean7.00,persistence10.70,momentum7.47. Różnica RF−mean−1.446pp; historyczny bootstrap blok6kwartałów CI[−2.015;−0.960]. Ale daty były eksplorowane i obejmują foldy strojenia: diagnostyka, nie niezależne potwierdzenie. Baseline liczy średnie logzmian per miasto w tym samym dojrzałym oknie. Źródła: reports/tables/scores.csv; paired_bootstrap.json.');
const hist=data.scores.filter(r=>r.phase==='historical_diagnostic'&&r.horizon===4);const order=['selected_model','historical_mean','momentum','no_change'];
chart(s,'bar',['RF','Średnia historyczna','Kontynuacja trendu','Ostatnia cena'],[{name:'MAPE (%)',values:order.map(m=>Number(hist.find(r=>r.model===m).MAPE_pct.toFixed(2))),fill:C.blue}],{yAxis:{minimumScale:0,numberFormatCode:'0.0'}});
text(s,'Diagnostyka retrospektywna; wcześniejsza eksploracja ogranicza siłę wniosku.',76,620,1110,38,20,false,C.muted);
s=slide('Ostatnia data: model traci przewagę','Origin 2025Q2 → cel 2026Q2 • 34 grupy • wyboru modelu nie zmieniono',
'60 s. Najważniejszy wynik negatywny: RF13.76%, mean13.41%, persistence3.88%. Model prognozuje wzrost17.1%, rzeczywisty3.1% od znanej ceny. Wszystkie34końcowe prognozy zawyżone. Zgodne z nadmierną kontynuacją wzrostu; nie dowód przyczynowości. Jedna data i wcześniej dostępne szeregi: nie dziewiczy holdout. Źródło: reports/tables/predictions.csv; scores.csv; README.');
const latest=data.scores.filter(r=>r.phase==='locked_test'&&r.horizon===4);
chart(s,'bar',['Wybrany RF','Średnia historyczna','Ostatnia cena'],[{name:'MAPE (%)',values:['rf_12_d6','historical_mean','no_change'].map(m=>Number(latest.find(r=>r.model===m).MAPE_pct.toFixed(2))),fill:C.orange}],{yAxis:{minimumScale:0,numberFormatCode:'0.0'}});
text(s,'Prognozowany wzrost: ~17,1%     Rzeczywisty wzrost: ~3,1%',76,620,1110,38,23,true,C.ink);
s=slide('Wyjaśniamy zachowanie modelu','Permutacje na ostatnim foldzie walidacji; dodatkowo lokalna analiza wrażliwości',
'40 s. Przemieszanie cechy i zmiana MAPE pokazuje użyteczność predykcyjną w foldzie. Nie jest efektem przyczynowym stóp, inflacji lub dopłat. Powiązane cechy dzielą znaczenie, a perturbacje mogą odchodzić od rozkładu. Local_sensitivity zastępujecechę medianą; nie nazywamy tego SHAP. Źródło: reports/tables/permutation_importance.csv i local_sensitivity.csv.');
const impNames={log_known_price:'Poziom znanej ceny',relative_price_known2:'Relacja ceny do mediany',local_yoy_known2:'Dynamika ceny r/r',local_qoq_known2:'Dynamika ceny k/k',local_yoy_acceleration_known2:'Przyspieszenie r/r',peer_yoy_known2:'Dynamika innych miast',market:'Rynek',area:'Miasto',policy_rate_lag1:'Stopa procentowa',inflation_yoy_lag1:'Inflacja',national_real_credit_flow_yoy_lag1:'Realny kredyt r/r',credit_count_yoy_lag2:'Liczba kredytów r/r',credit_count_acceleration_lag2:'Przyspieszenie kredytów',national_mortgage_rate_lag1:'Oprocentowanie hipotek',credit_count_qoq_lag2:'Liczba kredytów k/k',national_sloos_demand_lag1:'Popyt SLOOS',national_wage_yoy_lag1:'Płace r/r',policy_rate_change4q_lag1:'Zmiana stopy'};
impNames.hedonic_yoy_known='Indeks hedoniczny r/r';impNames.hedonic_qoq_known='Indeks hedoniczny k/k';
chart(s,'bar',data.importance.map(r=>impNames[r.feature]??r.feature),[{name:'Zmiana MAPE (pp)',values:data.importance.map(r=>Number(r.delta_MAPE_pp.toFixed(3))),fill:C.teal}],{barOptions:{direction:'bar'},position:{left:80,top:265,width:1100,height:360},dataLabels:{showValue:true,position:'outEnd'},xAxis:{numberFormatCode:'0.00',majorUnit:.02},yAxis:{numberFormatCode:'0.00',majorUnit:.02}});
s=slide('Demo: badawczy scenariusz dla miasta','API /predict + Pydantic oraz demonstrator Streamlit; Warszawa jako przykład',
'55 s, w tym demo. POST Warszawa/secondary zwraca5cen i znanykwartał; nieznane miasta dają422. Pokaż notebook03 lub live /docs. Wykres to snapshot2026Q3utworzony15.11po odniesieniu, wejściowa cena2026Q1, do2027Q3. h0 jestnowcastem. Brakskalibrowanychprzedziałów; nie wycena lokalu. Źródło: reports/tables/current_forecasts.csv; api/app.py; app.py.');
const qs=[...new Set(data.current.map(r=>r.target_quarter))];
chart(s,'line',qs,['primary','secondary'].map((m,i)=>({name:m==='primary'?'Pierwotny':'Wtórny',values:qs.map(q=>data.current.find(r=>r.market===m&&r.target_quarter===q).prediction_pln_m2),fill:i?C.teal:C.blue})),{yAxis:{numberFormatCode:'#,##0'}});
text(s,'Stały snapshot 2026Q3, przygotowany po tym kwartale; h0 to nowcast.',76,620,1110,38,20,false,C.muted);
s=slide('Odtwarzalność, testy i koszt obliczeń','Kod, dane, model i wyniki w jednym samodzielnym folderze',
'45 s. python -m src.pipeline all albo run.ps1 all; pytest. Testy obejmują dane, purging, eksport i API. Osobne środowisko; oryginalnyRF odtworzony. CPU2wątki, bezGPU, model456.6kB; czasrzeczywistyokoło.1snafit, zależnyodsprzętu. Nie mierzonenergii/CO2. Dockerfile orazCIprzygotowane, Docker lokalnie niedostępny, GitHub publicznydopublikacji. Źródła: reports/tables/green_it.json; tests; docs/REQUIREMENTS_MATRIX.md.');
bullets(s,['Jedno polecenie odtwarza dane, tuning, model i raport HTML.','Testy danych, chronologii, predykcji i błędnych żądań API.',`2 wątki CPU • bez GPU • model ${(data.green.model_bytes/1000).toFixed(1)} kB • fit ~${data.green.production_train_seconds.toFixed(2)} s`]);
s=slide('Wartość projektu i następny sprawdzian','Działający proces i jawne wyniki — także wtedy, gdy prosty baseline wygrywa',
'45 s. Podsumuj: pipeline jest odtwarzalny i możliwy do wyjaśnienia, historyczna poprawa istnieje, ale ostatni test jej nieutrzymuje. Nie sprzedajemy tego jako systeminwestycyjny. Kolejny krok: prospektywne nowe kwartały wedługzamrożonegoprotokołu. Ograniczenia: zrewidowane dane, miejskieśrednie, mało niezależnychcykli. Pytania5min. Źródła: README.md; docs/OBRONA.md.');
bullets(s,['Udało się: przygotować, porównać, odtworzyć i udostępnić prognozę.','Nie potwierdzono: stabilnej przewagi oraz wyceny pojedynczych lokali.','Dalej: nowe kwartały i ocena prospektywna według stałego protokołu.']);
if(deck.slides.items.length!==13)throw new Error('Expected13slides');
await fs.mkdir(path.join(tmp,'previews'),{recursive:true});
for(let i=0;i<13;i++){
 const blob=await deck.export({slide:deck.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(tmp,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const pdf=await deck.export({format:'pdf'});await fs.writeFile(path.join(out,'projekt_ceny_mieszkan.pdf'),new Uint8Array(await pdf.arrayBuffer()));
const candidate=path.join(tmp,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
const result=await finalizePresentation({workspaceDir:workspace,candidatePath:candidate,finalPath:path.join(out,'projekt_ceny_mieszkan_v3.pptx'),pythonExecutable:path.join(runtime,'python','python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:13,requiredNativeChartOwnerSlides:[4,7,8,9,10,11],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,materializeLiteralChartWorkbooks:true,receiptPath:path.join(tmp,'validation_v3.json')});
console.log(JSON.stringify({slides:13,output:out,validation:result},null,2));
