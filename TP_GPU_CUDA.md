# TP GPU CUDA — questions 35 à 40

Le script [gpu_bench.py](gpu_bench.py) compile [gpu_matmul.cu](gpu_matmul.cu), lance les quatre variantes du [notebook fourni](GPU_matmul_demo.ipynb) et rassemble les résultats CPU et GPU. Voir les pages 10 et 11 du [sujet](frugal_ai_practical_work_subject.pdf).

## 1. Campagne GPU sur Colab

Sélectionne un environnement GPU. Le TP vise un **NVIDIA T4**. Vérifie le modèle avec `!nvidia-smi` et le compilateur avec `!nvcc --version`.

```python
!git clone https://github.com/cctr002/frugal_ai.git
%cd /content/frugal_ai
!python gpu_bench.py gpu --max-size 256 --step 128 --repeats 1 --output gpu_smoke
```

Si le dépôt est déjà cloné, fais `!git pull origin main` dans son dossier. Si GitHub exige une authentification, téléverse une copie du dépôt dans la session Colab. Le petit test doit afficher des temps pour les quatre variantes. Lance ensuite la campagne complète.

```python
!python gpu_bench.py gpu
```

Le script détecte la cible CUDA. Sur un T4, tu peux aussi passer `--arch sm_75`. La grille par défaut va de **1024 à 16384**, par pas de **1024**, avec **trois mesures par point** après un échauffement. Le kernel naïf peut prendre du temps aux grandes tailles. Pour un essai intermédiaire, utilise `--max-size 4096 --output gpu_essai`. Pour le rapport final, utilise la même grille de tailles côté CPU et GPU.

Télécharge `gpu_results/gpu.csv` avant de fermer Colab. Tu peux aussi passer par une cellule Python avec `from google.colab import files` puis `files.download("gpu_results/gpu.csv")`.

## 2. Campagne CPU sur la machine du TP

Depuis la racine du dépôt sous Linux, avec **GCC et les en-têtes et bibliothèques OpenBLAS** disponibles, lance les commandes suivantes. Copie ensuite le `gpu.csv` téléchargé dans ton dossier local `gpu_results/`.

```bash
git pull origin main
python gpu_bench.py cpu
```

Le script mesure OpenBLAS à **un thread à N=4096**, puis essaie plusieurs nombres de threads et choisit le plus rapide à cette taille. Ce nombre reste fixe pour la courbe multicœur jusqu’à 16384. Tu peux l’imposer avec `--threads 12`, par exemple. Le nombre optimal pour v6 en Q30 peut différer de celui d’OpenBLAS. Le CSV CPU est enregistré dans `gpu_results/cpu.csv`. Prévois plusieurs Gio de RAM pour les plus grandes matrices.

## 3. Rapport et graphiques

Avec les deux CSV réunis dans `gpu_results/` et Matplotlib disponible dans ton environnement Python, lance le rapport. L’exemple utilise **70 W pour le T4 et l’hypothèse CPU de 70 W autorisée par l’énoncé**. Remplace ces chiffres par les puissances de référence que tu documentes si ton matériel ou ton hypothèse diffèrent.

```bash
python gpu_bench.py report --gpu-watts 70 --cpu-watts 70
```

| Question | Résultat généré | À interpréter |
| --- | --- | --- |
| **Q35** | Temps et GFLOP/s à 4096 pour cuBLAS FP32 et OpenBLAS en mono et multicœur. Accélérations GPU incluses. | Écart entre les trois configurations |
| **Q36** | `q36_cpu_gpu.png`, OpenBLAS multicœur et cuBLAS FP32 | Taille où le GPU prend l’avantage et évolution du débit |
| **Q37** | Meilleur GFLOP/J estimé par dispositif et taille associée | Puissance retenue et limites de l’hypothèse de puissance constante |
| **Q38** | Temps à 4096 et meilleur ratio du kernel naïf face à cuBLAS, avec la taille | Accès mémoire et réutilisation limitée |
| **Q39–40** | Temps à 4096, ratios, tailles des maxima et `q38_q40_cuda.png` | Comparer cuBLAS FP32, CUDA par tuiles et GemmEx. Q39 et Q40 répètent la consigne custom dans le PDF. Présenter aussi l’expérience GemmEx demandée dans le paragraphe suivant. |

Les débits utilisent **`2N³ / (temps × 10⁹)`**, comme la campagne OpenMP. La convention `N³` de certaines cellules du notebook donne des débits divisés par deux, avec les mêmes rapports d’accélération. Pour GemmEx, compare le rapport mesuré à taille égale au rapport des pics FP16 et FP32 cités pour le T4, environ 8×. Les CSV gardent le matériel, le nombre de répétitions, la moyenne et l’écart-type.

Les événements CUDA chronomètrent **le calcul avec les matrices déjà sur le GPU**. Les transferts, la transposition de A pour le kernel naïf et les conversions FP16 sont en dehors de cette fenêtre. Le programme vérifie toutes les cases à `N=64`, puis 36 cases pour chaque taille supérieure. GemmEx utilise des entrées et une sortie FP16 avec accumulation FP32. La référence numérique de cette variante part des mêmes entrées arrondies en FP16. Les ratios de Q37 divisent le débit par la puissance de référence fournie. Une mesure d’énergie réelle demande une mesure de puissance pendant le fonctionnement.
