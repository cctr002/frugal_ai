# Q34 — mesure de la puissance au wattmètre

L’objectif est de trouver le nombre de threads qui maximise le **travail effectué par joule** pour `matmul_v6`. Saisis tes mesures dans `openmp_results/Mesures_CPU_OpenMP.xlsx`. Les temps de calcul sont préremplis à partir de [Q30–Q32](openmp_results/q30_q32.csv).

## 1. Préparer la machine

1. Branche **la tour seule** sur le wattmètre. Garde le même écran et les mêmes périphériques pendant toute la campagne. Ferme les applications inutiles et utilise la machine sur laquelle Q30 a été mesurée. Si la machine ou les réglages changent, remesure les temps avant de les combiner aux watts.
2. Dans Excel, note la machine, la date et le périmètre. Attends **60 s au repos**, puis relève la puissance moyenne sur **30 s**. Cette valeur documente le contexte. Le calcul principal utilise la puissance totale de la tour, sans soustraire le repos.
3. Reprends la configuration du CSV : `N = 1920`, axe **M**, `schedule = static,1`, blocs **64, 120, 480**. Teste **1, 2, 4, 8, 12, 16, 20 et 24 threads**. La dernière valeur mesure l’effet du surabonnement.

## 2. Compiler une charge continue dédiée à v6

Depuis la racine du dépôt sous Linux, copie ce bloc dans le terminal. Le petit programme temporaire alloue les matrices une seule fois et répète v6. Ainsi, le wattmètre mesure une charge v6 continue. Le binaire de benchmark ordinaire exécute aussi OpenBLAS à chaque lancement.

```bash
q34_tmp=$(mktemp -d)
cat > "$q34_tmp/charge.c" <<'EOF'
#define main bench_main
#include "matmul.c"
#undef main

int main(void)
{
    const int n = 1920;
    float *a, *b, *c, *reference;
    create_matrices(&a, &b, &c, &reference, n, n, n);
    for (;;) {
        matmul_v6(a, b, c, n, n, n);
        __asm__ __volatile__("" : : "r"(c) : "memory");
    }
}
EOF
gcc -I "$PWD" -O3 -march=native -funroll-loops -ffast-math -fopenmp \
  -DV6_OMP_AXIS_N=0 -DBLOCK_M=64 -DBLOCK_N=120 -DBLOCK_K=480 \
  "$q34_tmp/charge.c" -o "$q34_tmp/charge" -lopenblas -lm
```

## 3. Faire les relevés

Pour chaque nombre de threads, réalise **trois passages**. Lance la commande suivante en remplaçant `p=1` par la valeur à mesurer. `timeout` arrête la charge au bout de 55 secondes.

```bash
p=1
OMP_NUM_THREADS="$p" OMP_DYNAMIC=FALSE OMP_SCHEDULE=static,1 OPENBLAS_NUM_THREADS=1 \
  timeout 55s "$q34_tmp/charge"
```

1. Attends **15 s** après le lancement pour stabiliser la charge.
2. Relève la **puissance moyenne entre t = 15 s et t = 45 s**. Si l’appareil n’affiche que la puissance instantanée, relève six valeurs à **20, 25, 30, 35, 40 et 45 s** et prends leur moyenne.
3. Saisis ce résultat dans la colonne du passage correspondant. Attends environ **30 s** entre passages. Si la puissance dérive encore au bout de 15 s, allonge la stabilisation et applique la même durée aux autres passages.
4. Identifie la ligne qui maximise les **GFLOP/J** et compare-la à celle qui maximise le **débit**. Le tableur calcule `énergie = puissance moyenne × temps moyen` et `efficacité = débit / puissance moyenne`.

Si tu veux aussi régénérer la figure Python, recopie les colonnes **threads** et **puissance moyenne** dans un fichier `watts.csv` avec l’en-tête `threads,watts`, puis lance `python openmp_bench.py --power-csv watts.csv`. Utilise des virgules comme séparateurs et des points pour les décimales dans ce fichier.
