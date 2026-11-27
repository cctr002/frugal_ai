# TP Frugal AI

## Partie 1 — Multiplier deux matrices

### Q1–2 · Machine et puissance au repos

Le poste de la salle est un **i7-12700** avec 8 cœurs P à deux threads et 4 cœurs E à un thread, soit **12 cœurs et 20 threads**. Il dispose de 15 Gio de RAM utilisable, d’AVX2 et de FMA. En FP32, un registre AVX2 contient huit nombres. Le L1 totalise 512 Kio de données et 512 Kio d’instructions. Les 12 Mio de L2 se répartissent en huit caches privés de 1,25 Mio et un cache de 2 Mio partagé par les quatre cœurs E. Les 25 Mio de L3 sont partagés.

| Situation | Veille | Repos écran éteint | Repos écran allumé | VS Code + Firefox | Ouverture d’un PDF | YouTube sans / avec accélération |
|---|---:|---:|---:|---:|---:|---:|
| Puissance à la prise | 1,7 W | 8 W | 16 W | 20 W | pic à 30 W | 28 / 27 W |

Allumer l’écran s’accompagne d’un écart de 8 W dans ce montage. Le wattmètre mesure ce qui est branché dessus. Les notes ne précisent pas le branchement de chaque périphérique. L’écart de 1 W sur YouTube est trop faible pour conclure sur un seul relevé. En monocœur, le sujet suppose le surcroît de puissance constant. Dans cette approximation, diviser le temps par deux divise aussi l’énergie de calcul par deux.

### Q3–8 · Python, Numba et NumPy

À **N = 512**, j’obtiens les temps suivants.

| Q3–5 | Trois boucles Python | Produit et somme NumPy dans la boucle | Trois boucles avec Numba | Produit et somme NumPy avec Numba |
|---|---:|---:|---:|---:|
| Temps | 27,510 s | 0,480 s | **0,062 s** | 0,130 s |

Déplacer la boucle interne dans NumPy donne un gain de **57×**. Numba accélère les trois boucles de **445×**, et la version avec somme NumPy de **3,69×**. Une fois compilée, la boucle simple évite de construire un vecteur intermédiaire pour chaque case de C.

**Q6–7.** Le débit de Numba baisse brutalement à certaines tailles, notamment à 1 024. Dans la boucle sur `k`, deux lectures successives de `B[k,j]` sont espacées de toute une ligne. À certaines tailles, ces adresses se disputent les mêmes ensembles du cache. En commençant à 96 au lieu de 128, les creux disparaissent presque. [Courbe initiale](6.png) · [Tailles décalées](7.png)

**Q8.** Les courbes de `@`, `np.matmul` et `np.dot` se rejoignent autour de 70 sur notre graphique. Les trois utilisent une multiplication matricielle optimisée pour ces tableaux FP32. Les figures Python et C séquentiel comptent **N³** opérations. Les figures OpenMP et GPU comptent **2N³** (une multiplication et une addition). Pour comparer deux campagnes, j’utilise les temps ou je ramène les débits à la même convention. [Courbes NumPy](8.png)

### Q9–20 · C, accès mémoire et vectorisation

Temps moyens à **N = 1 920**, en secondes. La dernière colonne utilise `-O3 -march=native -funroll-loops -ffast-math`. Les pourcentages ci-dessous comparent chaque version à OpenBLAS mesuré dans le même essai.

| Version | Sans option | -O1 | -O2 | -O3 | Toutes les options |
|---|---:|---:|---:|---:|---:|
| v1 · trois boucles | 18,386 | 12,243 | **5,394** | 5,459 | — |
| v2 · accumulateur | 12,948 | **4,791** | 4,923 | 5,257 | — |
| v3 · transposition de A | 12,093 | 2,958 | 2,887 | 2,936 | **0,477** |
| v4 · vecteurs de 8 floats | 11,893 | 1,754 | 1,677 | 1,723 | **0,473** |

**Q9–11.** Sans option, v1 atteint seulement **0,55 %** du débit d’OpenBLAS dans la série répétée. Passer à `-O2` divise le temps par 3,4. `-O3` apporte peu ici. À la même taille, Numba prend **8,508 s** en moyenne sur trois passages hors compilation. Il devance le C sans option (18,386 s), mais le C avec `-O2` passe devant (5,394 s). [Courbes v1 et v2](q11_13.png)

**Q12–13.** v2 accumule chaque produit dans une variable locale et écrit C une seule fois en fin de boucle. Le gain est surtout visible sans optimisation. Aux meilleurs réglages, on passe de 5,39 à 4,79 s. L’accès à une colonne avec un grand pas mémoire reste coûteux.

**Q14–15.** Le code C stocke les matrices colonne par colonne. Transposer A permet de lire à la suite les valeurs de A et B nécessaires au produit scalaire. Avec `-O2`, on passe de 4,92 à 2,89 s, transposition comprise. [Courbes v3](q15_17.png)

**Q16–17.** À 1 920, ajouter uniquement `-march=native` ou `-funroll-loops` à `-O3` laisse v3 près de 2,9 s. Avec `-ffast-math`, le compilateur peut réassocier la somme et on descend à **0,794 s**. Les trois options ensemble donnent **0,477 s**, soit **21 % d’OpenBLAS**. À 4 096, la courbe optimisée tombe à **7,0** contre **70,3** pour OpenBLAS. Les deux vecteurs sont contigus, mais on les relit pour chaque nouveau produit scalaire.

**Q18–20.** v4 charge huit floats de A transposée et huit de B, multiplie les huit paires puis accumule dans huit sommes partielles. À la fin, on additionne ces huit sommes pour obtenir une case de C. Avec `-O2`, v4 prend 1,68 s contre 2,89 s pour v3. Avec toutes les options, **0,473 et 0,477 s** sont pratiquement identiques. Écrire soi-même les vecteurs apporte peu quand le compilateur vectorise déjà bien la boucle. [Courbe v4 et OpenBLAS](q20.png)

### Q21–27 · Réutiliser les données dans les registres et les caches

**Q21–23.** v5 calcule une tuile de C. Un vecteur de A sert à plusieurs colonnes, et un scalaire de B à plusieurs lignes. Les sommes partielles restent dans des registres pendant le parcours de K. À 1 920, v5 prend **10,58 / 3,61 / 5,22 / 4,76 s** sans option puis avec `-O1/-O2/-O3`. Avec toutes les options, elle descend à **0,249 s**, soit **41 % d’OpenBLAS**. À 3 840, elle atteint seulement **10,1** contre **73,6** pour OpenBLAS. La tuile améliore la réutilisation locale, mais les accès aux grandes matrices restent coûteux. [Courbe v5](q23.png)

**Q24.** Une tuile de hauteur H et de largeur W demande `(H/8) × W` accumulateurs vectoriels, auxquels s’ajoutent les registres des opérandes.

| Tuile | Accumulateurs | N = 240 | N = 1 920 |
|---|---:|---:|---:|
| 8 × 6 | 6 | 0,551 ms | 310 ms |
| 16 × 6 | 12 | 0,527 ms | **242 ms** |
| 16 × 8 | 16 | 0,605 ms | 251 ms |

À 240, les écarts sont petits devant la dispersion. À 1 920, je retiens **16 × 6**. Agrandir encore la tuile augmente la pression sur les registres.

**Q25–27.** v6 découpe aussi M, N et K en blocs. On réutilise ainsi les données en cache pour plusieurs appels au kernel. Dans la même série à 1 920, v4 prend **466 ms**, v5 **228 ms**, v6 **136 ms**. Parmi les dix découpages testés, **64/120/480** donne la meilleure moyenne, **133,4 ± 4,9 ms**, soit **77 % d’OpenBLAS**. Le découpage 64/120/240 est proche à 134,9 ms. À 3 840, v6 conserve **51,4** contre **73,9** pour OpenBLAS, alors que v5 est à **10,0**. [Courbes v4 à v6](q27.png)

### Q28–34 · OpenMP et énergie

**Q28–29.** Chaque thread reçoit des blocs distincts de C et garde toutes leurs contributions sur K. Deux threads qui feraient `C[i,j] += …` en même temps pourraient perdre une contribution. Dans la campagne des figures, à deux threads, l’axe M donne **73,4 ms** contre **77,3 ms** sur N. Sur M, `static,1` donne **66,5 ms**, `guided,2` **67,1 ms** et `dynamic,1` **69,1 ms**. Le travail est assez régulier pour une répartition statique. Une autre campagne dans les notes favorise N avec `static,4` ; les écarts dépendent du passage. [Mesures par axe et par schedule](openmp_results/q28_q29.csv)

**Q30–32.** Avec M, `static,1` et les blocs 64/120/480, le débit passe de **109 GFLOP/s à 1 thread** à **444 à 8**, puis **600 à 20**. À 24 threads il retombe à **476**. Le poste expose 20 threads matériels. En ajouter quatre fait partager les mêmes ressources à davantage de threads. Les deux courbes de speedup se superposent presque parce que les références sont très proches **(130,54 ms sans OpenMP et 129,96 ms avec un thread)**. À 20 threads, les gains correspondants sont **5,53× et 5,51×**. [Débit](openmp_results/q30.png) · [Speedup](openmp_results/q32.png)

**Q33.** Si la puissance double, `E(12)/E(1) = 2 × t(12)/t(1)`. Dans la campagne consignée dans les notes, ce rapport vaut **0,645 pour v6** et **0,647 pour OpenBLAS**. On économise environ **35 % d’énergie** dans les deux cas. La campagne de la figure Q30, avec d’autres réglages, donne **0,457 pour v6**.

**Q34.** À **N = 9 600**, le wattmètre donne 20 W au repos. En charge, les relevés sont les suivants.

| Threads | 1 | 2 | 4 | 8 | 12 | 16 | 20 | 24 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Puissance (W) | 63 | 86 | 136 | 171 | 170 | 162 | 157 | 166 |
| Temps v6 (s) | 19,77 | 10,13 | 6,77 | 5,05 | 4,99 | 4,99 | **4,70** | 5,08 |
| GFLOP/J à la prise | 1,42 | 2,03 | 1,92 | 2,05 | 2,09 | 2,19 | **2,40** | 2,10 |

**20 threads donnent à la fois le meilleur temps et le meilleur rendement.** À 8 threads le poste consomme davantage (171 W contre 157 W) pour un calcul plus lent. Si je soustrais les 20 W au repos, le maximum reste à 20 threads, avec **2,75 GFLOP/J**. Ce calcul associe deux passages à 9 600 sur le même poste et suppose que les watts stabilisés ont été relevés pendant v6. [Temps et puissances](openmp_results/q34_9600_ePspKC.csv)

### Q35–40 · CPU contre T4

**Q35.** À N = 4 096, voici le temps moyen de trois multiplications. Sur le T4, les matrices sont déjà en mémoire GPU et le chronométrage exclut les transferts.

| Version | Temps | GFLOP/s |
|---|---:|---:|
| OpenBLAS CPU, 1 thread | 971,4 ms | 141 |
| OpenBLAS CPU, 8 threads | 160,4 ms | 857 |
| cuBLAS T4, FP32 | **33,3 ms** | **4 128** |
| CUDA naïf | 3 052,1 ms | 45 |
| CUDA par tuiles | 64,8 ms | 2 121 |
| GemmEx, entrées FP16 et accumulation FP32 | **2,77 ms** | **49 574** |

**Q36.** À 4 096, cuBLAS FP32 est **29,2×** plus rapide qu’OpenBLAS à un thread et **4,8×** plus rapide qu’à huit threads. Le T4 est déjà devant à la première taille testée (1 024). À 16 384, il atteint **4 080 GFLOP/s**, contre **684** sur CPU. [Courbe CPU et T4](gpu_results/q36_cpu_gpu.png)

**Q37.** Avec la puissance turbo maximale publiée du i7-12700 (**180 W**), le CPU atteint au mieux **857/180 = 4,76 GFLOP/J**, à 4 096. Avec les **70 W** du sujet, le T4 en FP32 atteint **7 377/70 = 105,4 GFLOP/J**, à 2 048. Le rapport estimé vaut **22×**. Ces chiffres utilisent une puissance constante sur toute la courbe. [Fiche Intel](https://www.intel.com/content/www/us/en/products/sku/134591/intel-core-i712700-processor-25m-cache-up-to-4-90-ghz/specifications.html)

**Q38.** Chaque thread du kernel naïf calcule une seule case de C et relit deux valeurs à chaque tour sur K. Son meilleur résultat relatif est **1,09 % de cuBLAS**, à 4 096. À cette taille, même OpenBLAS sur un seul thread le devance.

**Q39.** Le kernel par tuiles partage les données d’un bloc et conserve plusieurs sommes en registres. À 4 096, il est **47×** plus rapide que le naïf et atteint **51 % de cuBLAS**. Son meilleur rapport est **64 % à 1 024**. Son débit maximal arrive à 2 048, puis retombe de 3 192 à 1 636 GFLOP/s entre 2 048 et 16 384.

**Q40.** GemmEx atteint son meilleur débit à **5 120** (49,9 TFLOP/s), contre **2 048** pour cuBLAS FP32 (7,38 TFLOP/s). À 5 120, GemmEx est **13,6×** plus rapide que cuBLAS FP32. Ce chiffre dépasse le rapport théorique des pics (environ 8×) parce qu’à cette taille le FP32 mesuré est déjà loin de son pic. Si on compare les deux meilleurs débits mesurés, le rapport vaut **6,8×**. [Courbes des quatre kernels](gpu_results/q38_q40_cuda.png) · [Mesures du T4](gpu_results/gpu.csv)

## Partie 2 — Reconnaître les chats et les chiens

J’ai gardé le découpage ASIRRA du TP et les mêmes 2 048 images pour comparer les modèles. L’objectif est d’obtenir la meilleure accuracy **en moins de 300 ms sur le T4**. Les essais CPU avaient un budget local de 5 s.

| Essai | Idée testée | Accuracy observée | Inférence |
|---|---|---:|---:|
| 1 · CPU | Images 64 × 64, deux convolutions puis trois couches denses | 83,89 % à 500 itérations | 0,70 s |
| 2 · CPU | Cinq convolutions, augmentations plus fortes et dropout réduit | **92,92 %** à 500 | 3,63 s |
| 3 · CPU | Plus de convolutions sur de petites cartes, moyenne globale et aucune couche dense | **90,48 % au checkpoint 100**, entraînement arrêté | 2,70 s |
| 4 · T4 | Images 96 × 96, première convolution de stride 2, entraînement et inférence en précision mixte | **89,70 % à 150** en validation, **50,00 % à 500** | **154,5 ms** au checkpoint 500 |
| 5 · T4 | Même architecture, entraînement FP32, inférence en précision mixte et sauvegarde du meilleur checkpoint | **94,29 %** au meilleur checkpoint (500), après **15,09 min** | **136,1 ms** |
| 6 · T4 | Images 128 × 128 au lieu de 96 × 96, architecture et entraînement de la config 5 | **95,56 %** au checkpoint 450 (500 itérations en **17,90 min**) | **244,9 ms** |
| 7 · T4 | Comme la 6, mais rotation et changement d’échelle appliqués à 60 % des images au lieu de 30 % | À mesurer | À mesurer |

Sur CPU, la config 1 finit par plafonner autour de 84 % alors que sa perte d’entraînement baisse encore. Avec la config 2, la perte de validation passe de 0,356 à 0,224 et l’accuracy continue de monter. La config 3 était encore en progression à son arrêt. À quantité de données vue égale (409 600 images), elle atteint 90,48 % contre 87,21 % pour la config 2 et 89,26 % pour la config 4.

Sur T4, la config 4 tient le budget de temps. À partir de l’itération 250, les pertes d’entraînement et de validation augmentent ensemble. À 400, le réseau prédit « chat » pour les 2 048 images. Cela indique une instabilité d’entraînement. Avec la config 5, la validation remonte de 89,40 % à l’itération 200 à 94,29 % à 500. À 128 × 128, la config 6 gagne encore 1,27 point et reste sous 300 ms. Elle progresse de 94,68 % à 250 itérations à 95,56 % à 450, puis finit à 95,51 %. La config 7 teste l’effet d’une augmentation géométrique plus fréquente. [Logs des essais](notes.md)

**Modèle retenu à ce stade.** Je garde le checkpoint 450 de la config 6. Il classe correctement 95,56 % des images en 244,9 ms, soit 55,1 ms sous le budget. Le résultat de la config 7 reste à intégrer avant le choix définitif et la remise des poids.
