# OpenMP et CUDA — guide des questions 28 à 40

Le TP passe de **SIMD sur un cœur CPU** à deux formes de parallélisme. Avec OpenMP, plusieurs threads CPU exécutent chacun des blocs de `matmul_v6`, et chaque thread peut continuer à utiliser le SIMD. Avec CUDA, beaucoup de threads GPU se répartissent les éléments ou les tuiles de la matrice résultat.

Sources du TP : [énoncé, p. 9–11](frugal_ai_practical_work_subject.pdf), [slides 60–75](frugal_ai.pdf), [notebook GPU](GPU_matmul_demo.ipynb). Le code CPU de départ est dans [matmul.c](matmul.c) et ses mesures passent par [C_python_wrapper.py](C_python_wrapper.py).

## 1. Le point commun — chaque tâche possède une région de C

Pour `A` de taille `M × K` et `B` de taille `K × N`, le calcul est `C[i,j] = somme_k(A[i,k] × B[k,j])`. En stockage par colonnes, `C[i,j]` se trouve à l’indice `i + j*M`.

Deux tâches qui calculent des zones disjointes de C peuvent avancer en parallèle. Elles peuvent lire les mêmes A et B, puisque ces entrées restent en lecture seule. Dans v6, chaque bloc de `K` fournit en revanche une **somme partielle de la même tuile de C**. Les sommes partielles d’une tuile doivent être combinées. C’est cette distinction qui guide toute la parallélisation.

```text
Pour chaque bloc de lignes i0 et de colonnes j0 :
    réserver à cette tâche la tuile C[i0:i1, j0:j1]
    pour chaque tranche k0:k1 :
        ajouter A[i0:i1, k0:k1] × B[k0:k1, j0:j1] à cette tuile
```

## 2. OpenMP — distribuer les blocs de v6 sur le CPU

Une directive `#pragma omp parallel for` demande au compilateur de créer une région parallèle et de répartir les itérations de la boucle suivante entre les threads. Avec GCC, compiler **et lier** avec `-fopenmp`. Un thread OpenMP est une unité d’exécution logicielle que le système place sur un processeur logique. Les notes du TP indiquent **12 cœurs physiques et 20 processeurs logiques** sur l’i7-12700 de la salle, avec des P-cores et des E-cores. Un nombre de threads identique ne garantit pas un placement ni une puissance de calcul identiques.

### Q28 — comparer la boucle M et la boucle N avec deux threads

Pour paralléliser **M**, placer la directive juste avant la boucle sur les blocs de lignes. Voici le squelette à adapter aux noms de v6. Les bornes par `min` sont à écrire comme dans v6, avec un opérateur ternaire ou une fonction équivalente.

```c
/* Mettre C à zéro une fois avant la région parallèle. */
#pragma omp parallel for default(none) schedule(static) shared(A, B, C, M, N, K, l3, l2, l1)
for (int i = 0; i < M; i += l3) {
    for (int j = 0; j < N; j += l2) {
        for (int k = 0; k < K; k += l1) {
            /* Calculer i_stop, j_stop et k_stop comme dans v6. */
            /* Appliquer kernel à chaque microtuile, sur [k, k_stop). */
        }
    }
}
```

Pour tester **N**, mettre la boucle des colonnes `j` en premier, puis `i`, puis `k`, et placer la directive avant `j`. Déclarer les indices et les bornes temporaires dans les boucles, de sorte que chaque thread ait ses propres variables. Avec les déclarations actuelles de v6 (`int i,j,k;`), copier seulement le `#pragma` laisserait les indices des boucles internes potentiellement partagés. Le kernel possède déjà ses propres accumulateurs locaux. Chaque thread doit conserver **tout le parcours de K** pour les tuiles dont il est responsable.

| Répartition | Ce que chaque thread écrit | Données d’entrée que plusieurs threads peuvent relire |
| --- | --- | --- |
| M en parallèle | Des bandes de lignes de C | Les mêmes colonnes de B |
| N en parallèle | Des bandes de colonnes de C | Les mêmes lignes de A |

Le passage d’un bloc à l’autre change les accès aux caches privés et partagés. En stockage par colonnes, les bandes de colonnes de C forment des zones contiguës. Des bandes de lignes peuvent partager une ligne de cache à une frontière mal alignée. Le phénomène s’appelle *false sharing* si deux threads écrivent dans des cases différentes de cette même ligne. L’équilibrage compte aussi. Avec beaucoup de threads et peu de blocs sur l’axe choisi, des threads peuvent rester sans travail. Par exemple, avec `bN = 120` et `N = 1920`, la boucle N ne comporte que 16 itérations. Enfin, les E-cores se partagent un L2 sur la machine décrite dans les notes. L’explication « un L2 privé par cœur » est donc à nuancer pour ce CPU.

Ne pas distribuer directement `k` entre threads avec le kernel actuel. Ses écritures `C[...] += ...` sur la même tuile entraîneraient une course. Une telle variante nécessiterait des résultats partiels privés et une réduction, avec du travail et des transferts supplémentaires.

### Q29 — tester l’attribution du travail

| Option | Répartition | Effet à examiner |
| --- | --- | --- |
| `static` | Répartition fixée au départ, généralement en groupes contigus sans taille explicite | Peu de surcoût et bonne base pour des tuiles régulières |
| `static,1` | Attribution cyclique, par groupes d’une itération | Peut mieux répartir certaines variations, modifie la localité |
| `dynamic,1` | Un thread redemande une itération quand il se libère | Peut aider en cas de déséquilibre, avec davantage de coordination |
| `guided,1` | Groupes distribués à la demande, de taille décroissante | Cherche un compromis entre coordination et équilibrage |

Le deuxième argument est une taille de groupe **en itérations de la boucle**, donc en blocs externes ici. Tester par exemple `1`, `2` et `4`, sauf si la boucle a trop peu d’itérations. Pour éviter de recompiler à chaque essai de stratégie, utiliser `schedule(runtime)` puis fixer `OMP_SCHEDULE`.

### Q30–32 — mesurer le débit et l’accélération

Exemple de lancement Linux pour une v6 à laquelle la directive a été ajoutée avec `schedule(runtime)`, avec les mêmes tailles de blocs et les mêmes flags d’optimisation en référence et en parallèle.

```bash
gcc matmul.c -O3 -march=native -funroll-loops -ffast-math -o matmul_seq -lopenblas -lm
gcc matmul.c -O3 -march=native -funroll-loops -ffast-math -fopenmp -o matmul_omp -lopenblas -lm
OPENBLAS_NUM_THREADS=1 ./matmul_seq 1920 matmul_v6
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 OMP_SCHEDULE=static ./matmul_omp 1920 matmul_v6
```

Ajouter les mêmes `-DBLOCK_M=… -DBLOCK_N=… -DBLOCK_K=…` aux deux compilations si Q26 a retenu des valeurs différentes des défauts. Garder `OPENBLAS_NUM_THREADS=1` pour la validation et la référence série. Pour mesurer une **référence OpenBLAS multicœur**, faire une campagne séparée où l’on change explicitement ce réglage et où l’on relève le nombre de threads. Le wrapper fixe actuellement **les deux variables à 1**, donc lancer `OMP_NUM_THREADS=8 python C_python_wrapper.py` ne suffit pas. Il faut transmettre la valeur choisie à l’environnement du sous-processus ou appeler le binaire directement.

1. **Q30** — Fixer `N = 1920`, la version, les blocs et le scheduling retenu. Tracer le débit en fonction des threads. Répéter et noter moyenne et dispersion. Essayer `1, 2, 4, 8, 12, 16, 20, 24` sur la machine des notes pour couvrir cœurs physiques, processeurs logiques et surabonnement.
2. **Q31** — Comparer `T_seq`, compilé sans OpenMP, à `T_omp(1)`, compilé avec OpenMP et exécuté avec un thread. Leur écart inclut les coûts de la région parallèle et d’éventuels effets du code généré.
3. **Q32** — Tracer `S_seq(p) = T_seq / T_omp(p)` et `S_omp(p) = T_omp(1) / T_omp(p)`. Le texte de Q31 décrit le ratio inverse. Avec la convention usuelle ci-dessus, un résultat de `2` signifie deux fois plus rapide. Si le rendu suit littéralement l’énoncé, étiqueter l’autre ratio comme **temps normalisé** `T_omp(p) / T_ref`.

Un plateau peut venir du nombre de tuiles, de la bande passante mémoire, des caches, des synchronisations ou de fréquences plus faibles quand plusieurs cœurs travaillent. Le placement entre P-cores, E-cores et threads matériels peut aussi changer la courbe. Consigner le placement si on le fixe et garder les mêmes réglages pour les comparaisons.

### Q33–34 — relier temps, puissance et énergie

Avec `E = P_moyenne × T`, si le passage de 1 à `p` cœurs double la puissance, `E_p / E_1 = 2 × T_p / T_1 = 2 / S(p)`. Exemple fictif avec une accélération de `4` : la puissance double et la durée est divisée par quatre, donc l’énergie par produit est divisée par deux. Faire le même calcul pour OpenBLAS avec ses propres temps.

Pour Q34, mesurer la puissance avec le wattmètre pendant une séquence assez longue de produits identiques. Relever le repos et préciser si le calcul utilise la puissance de la machine entière ou le surplus au-dessus du repos. Avec un périmètre constant, `GFLOP/s ÷ W` donne des `GFLOP/J`. Chercher le nombre de threads qui maximise cette quantité. Faire coïncider ce que couvre la puissance avec la phase couverte par le temps de calcul.

## 3. CUDA — de la matrice C à la grille de threads

Le **host** est le CPU qui prépare les entrées et lance le calcul. Le **device** est le GPU qui exécute le kernel. Un lancement CUDA crée une **grille** de **blocs** de threads. Chaque bloc est affecté à un multiprocesseur de flux (**SM**), où les threads sont exécutés par groupes de 32 appelés **warps**. Les threads d’un même bloc peuvent coopérer via la mémoire partagée. Le code du kernel s’exécute pour chaque thread, qui connaît ses coordonnées via `threadIdx`, `blockIdx` et `blockDim`.

| Espace | Ce qui y vit dans le TP |
| --- | --- |
| VRAM, mémoire globale | A, B, C en entier, accessibles à tous les blocs |
| Cache L2 du GPU | Données réutilisées par les SM, avec gestion matérielle |
| Mémoire partagée d’un bloc | Tuiles d’A et B que les threads chargent ensemble et réutilisent |
| Registres d’un thread | Fragments et sommes partielles, tant que la pression sur les registres le permet |

**Coalescence** : à une instruction de lecture donnée, les accès de threads voisins d’un warp peuvent être regroupés en moins de transactions s’ils visent des adresses proches. **Divergence** : des branches différentes dans un même warp peuvent réduire le nombre de threads utiles exécutés ensemble. **Occupancy** : part des warps que le SM peut garder actifs. Beaucoup de registres ou de mémoire partagée par bloc peuvent limiter cette capacité, même si ces ressources accélèrent localement le calcul.

## 4. Lire les quatre variantes de `GPU_matmul_demo.ipynb`

Dans le notebook, les cellules `%%writefile` écrivent des fichiers `.cu`, puis les cellules suivantes les compilent avec `nvcc` et exécutent le binaire. Vérifier le GPU réellement alloué (`nvidia-smi`) avant de relever les temps. L’énoncé vise une **T4** et le notebook utilise `-arch=sm_75`. Consigner le GPU utilisé et adapter la cible si nécessaire.

### Q35–37 — cuBLAS FP32

`cublasSgemm` calcule `C = alpha × A × B + beta × C`. Le notebook choisit `alpha = 1`, `beta = 0`, travaille en FP32 et commence par un appel d’échauffement. Les allocations et transferts sont placés en dehors de la fenêtre chronométrée par événements CUDA.

1. **Q35** — Mesurer à `N = 4096`. Comparer avec OpenBLAS à un thread puis avec OpenBLAS au nombre de threads retenu en Q34 ou, à défaut, avec le meilleur débit mesuré. Relever le temps et le débit.
2. **Q36** — Tracer les deux courbes jusqu’à `16384`, avec les mêmes abscisses et le même comptage d’opérations. Un pas de `512` ou `1024` donne des dimensions compatibles avec le kernel custom. À `16384`, trois matrices FP32 occupent déjà **3 Gio** côté GPU, hors allocations internes et copies CPU.
3. **Q37** — Diviser chaque débit par la puissance de référence retenue. Avec une puissance constante par appareil, le maximum de `GFLOP/s/W` se situe au même point que le maximum de `GFLOP/s`. Une puissance crête issue des caractéristiques du matériel, ou les 70 W de substitution permis par l’énoncé, donne une **estimation**. Documenter le périmètre et distinguer ce ratio de la comparaison au wattmètre de Q34.

### Q38 — kernel naïf, un thread par élément de C

Le notebook lance des blocs de 256 threads. Chaque thread identifie sa case de sortie puis exécute sa propre boucle sur `k`.

```text
c_id = blockIdx.x * blockDim.x + threadIdx.x
si c_id >= M*N : sortir
row = c_id % M
col = c_id / M           (division entière)
acc = somme_k(A_T[row*K + k] * B[col*K + k])
C[c_id] = acc
```

La transposition de A rend le parcours en `k` contigu **pour un thread pris seul**. Mais à une valeur de `k` fixée, les threads voisins calculant des lignes différentes lisent `A_T` avec un pas de `K`. Les deux niveaux de localité peuvent donc se contredire. Les threads peuvent partager des lectures de B via le matériel, mais ce kernel ne charge aucune tuile explicitement en mémoire partagée. La sortie est contiguë entre threads voisins. Dans le notebook, l’expression `B[col*N + k]` fonctionne pour les essais carrés où `K == N`. Pour un test rectangulaire, l’indice attendu est `B[col*K + k]`.

Mesurer à `4096`, puis comparer sur la même grille de tailles que cuBLAS. Le meilleur pourcentage se calcule pour une taille donnée, avec `100 × T_cuBLAS(N) / T_naif(N)`. Relever le maximum et sa taille.

### Q39–40 — kernel custom inspiré de CUTLASS

| Niveau | Découpage du notebook | Travail réalisé |
| --- | --- | --- |
| Bloc CUDA | Une tuile `64 × 64` de C, tranches de `K` de taille `4` | Charge à chaque tranche des morceaux de A et B dans `As` et `Bs` |
| Warp | Une sous-tuile `32 × 16` | Les 32 threads se répartissent les éléments à calculer |
| Thread | Un fragment `4 × 4` de C | Réutilise 4 valeurs de A et 4 de B pour 16 mises à jour de ses accumulateurs |

Les barrières `__syncthreads()` permettent aux membres d’un bloc de lire des tuiles complètement chargées et d’empêcher leur écrasement avant la fin de la phase de calcul. Les accumulateurs restent locaux à chaque thread, puis C est écrite quand toutes les tranches de K ont été traitées. Le principe ressemble à v6 : fractionner K et réutiliser les données. Ici, le programme pilote explicitement les chargements dans la mémoire partagée et la synchronisation.

Le kernel custom du notebook utilise une grille calculée par divisions entières. Pour comparer ses résultats, choisir **M et N multiples de 64** et **K multiple de 4**. Sans traitement explicite des bords, des dimensions incompatibles laissent des résultats incomplets. Mesurer à `4096`, tracer le débit sur la grille de Q36 et relever le maximum de `100 × T_cuBLAS(N) / T_custom(N)` avec sa taille. Les pourcentages donnés dans le notebook sont des indications, à vérifier sur le GPU du TP.

**Ambiguïté de l’énoncé** : Q39 et Q40 ont le même texte, puis vient le paragraphe sur les Tensor Cores. Une lecture pratique est de faire la comparaison custom pour Q39 et de présenter aussi le test `GemmEx` demandé à la suite dans la section Q40.

### Complément de l’énoncé — Tensor Cores et précision mixte

Le notebook utilise `cublasGemmEx` sur des entrées **FP16**, avec accumulation **FP32** et sortie **FP16**. Les Tensor Cores sont des unités spécialisées dans les opérations matricielles. Dans cette variante, moins d’octets sont nécessaires pour stocker les matrices, et les opérations peuvent bénéficier d’unités à plus haut débit. L’accumulation FP32 limite certains arrondis, mais les entrées et la sortie restent arrondies en FP16.

Tracer le débit sur la même grille et calculer `T_FP32(N) / T_GemmEx(N)`. Comparer les tailles où les courbes plafonnent et le gain mesuré au rapport des débits crête indiqués dans l’énoncé pour la T4. Le gain dépend aussi des tailles, du trafic mémoire et du choix de kernel par cuBLAS. Vérifier l’écart numérique sur les **mêmes entrées** avec une tolérance adaptée et consigner séparément le coût des conversions et transferts si le scénario d’usage les inclut.

## 5. Protocole commun et figures à rendre

- **Débit** — Le wrapper et le notebook utilisent `N³ / (T × 10⁹)`. Le comptage usuel de GEMM est proche de `2N³` si multiplication et addition comptent séparément. Garder `N³` pour prolonger les courbes antérieures, ou recalculer **toutes** les séries avec `2N³`. Indiquer la convention sur la figure et utiliser `2N³` pour comparer aux pics matériels exprimés selon le comptage usuel. Les ratios entre implémentations restent les mêmes.
- **Chronométrage GPU** — Les événements `start` et `stop` encadrent le travail GPU, puis `cudaEventSynchronize(stop)` attend la fin. `cudaEventElapsedTime` renvoie des millisecondes. Le notebook divise par 1000 pour imprimer des secondes. Les copies CPU↔GPU et la transposition CPU de la variante naïve sont hors de cette mesure. Pour un temps de bout en bout, mesurer les préparations, les copies, le calcul synchronisé et la récupération de C dans une expérience séparée.
- **Échauffement et vérification** — Les variantes cuBLAS ont déjà un appel préalable. Pour rendre la comparaison plus homogène, échauffer aussi les kernels naïf et custom et répéter les mesures. Les binaires GPU du notebook impriment surtout le temps, avec des initialisations différentes entre variantes. Pour valider les résultats, fournir les mêmes matrices et comparer C à une référence, notamment sur petites tailles et en précision mixte. Contrôler les erreurs CUDA et cuBLAS avant de garder un temps.
- **Figures CPU** — GFLOP/s selon le nombre de threads, deux courbes d’accélération, puis GFLOP/J ou GFLOP/s/W selon le nombre de threads. Garder le tableau M/N et scheduling pour expliquer le choix.
- **Figures GPU** — Débit selon la taille pour OpenBLAS multicœur, cuBLAS FP32, CUDA naïf, CUDA custom et GemmEx. Indiquer le matériel, la précision et le périmètre. Présenter les comparaisons à 4096, les maxima relatifs à cuBLAS et leurs tailles, puis l’estimation énergétique.
- **Colonnes de mesure** — Pour chaque ligne, garder la version, la taille, le nombre de threads CPU ou le GPU, les flags, le temps moyen, l’écart-type, le débit et la puissance si disponible. Les interprétations du rapport doivent partir de ces mesures.
