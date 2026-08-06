# Auditoría empírica y estadística de TerraRover-Gen

Fecha: 2026-08-06  
Objetivo editorial: *Robotica* (Cambridge University Press)  
Alcance: proyecto Unity completo, con especial atención a `results/`, `Scripts_Analysis/`, configuración de Unity/ML-Agents, modelos, escenas, prefabs y definiciones de terreno.

## 1. Conclusión ejecutiva

La base empírica primaria es utilizable para el paper, pero los JSON/tablas generados por los scripts estadísticos históricos no deben reutilizarse como fuente de cifras. Los CSV contienen un conjunto primario internamente consistente de 100 episodios por sistema y terreno, y las tasas de éxito y los p-valores de McNemar se reproducen. Sin embargo, se han confirmado errores en los intervalos de confianza de diferencias pareadas y en el tamaño de efecto de Wilcoxon, además de problemas de trazabilidad y varias decisiones analíticas que deben corregirse para el manuscrito.

Decisión principal: `Complete` debe analizarse con los 100 episodios brutos como resultado primario. El filtrado histórico de 37 episodios se conservará, como máximo, como análisis de sensibilidad.

## 2. Inventario y genealogía de datos

Se localizaron 969 archivos en el proyecto. Los datos de evaluación relevantes están concentrados en:

- `results/EvaluationResults/RL/`
- `results/EvaluationResults/Heuristic/`
- `Scripts_Analysis/OE8/`
- `Scripts_Analysis/OE9/`

Las copias de CSV presentes en `Scripts_Analysis/` son, salvo una excepción importante, idénticas byte a byte a las de `results/EvaluationResults/`.

Excepción: `results/EvaluationResults/RL/HuskyAgent2_metricas_V3_F3_02.csv` contiene solo la cabecera, mientras que `Scripts_Analysis/OE9/HuskyAgent2_metricas_V3_F3_02.csv` contiene los 100 episodios del RL baseline V3. Por tanto, para reconstruir el conjunto primario es necesario usar esta copia de OE9 como fuente del RL V3.

El directorio OE8 tampoco contiene las copias heurísticas que su script espera encontrar en el directorio de trabajo. En su estado actual, el análisis OE8 no es reproducible directamente desde `Scripts_Analysis/OE8/` sin reunir antes los CSV desde `results/EvaluationResults/Heuristic/` y el RL V3 de OE9.

Archivos no aptos para el análisis primario:

- `HuskyAgent2_metricas_pruebaVideo1.csv`: 7 episodios de demostración.
- `HuskyHeuristic_metricas_pruebaVideo1.csv`: vacío.
- `HuskyAgent2_metricas_TerrainSticky_BumpyGround_FL2000.csv`: vacío.
- `results/EvaluationResults/RL/HuskyAgent2_metricas_V3_F3_02.csv`: vacío; se sustituye exclusivamente para el análisis por la copia completa conservada en OE9.

## 3. Integridad de los seis datasets primarios

Para V3_F3_02, BigRock, HardTerrain, BumpyGround, Complete y DeepHoles se verificó:

- 100 episodios RL y 100 heurísticos por terreno;
- identificadores `episodio=1..100`, sin duplicados ni huecos;
- `tasa_exito_acum` coherente fila a fila con los resultados observados;
- ningún `SUCCESS` con `distancia_final_m > 2 m`;
- `tiempo_s` coherente con `pasos * 0.01 s` dentro de la precisión de registro;
- categorías terminales primarias observadas: `SUCCESS`, `STUCK`, `FALL`, `COLLISION`; no aparece `SPIN` ni `COLLISION_STAY` en los seis datasets primarios.

## 4. Resultados primarios regenerados desde CSV bruto

Los IC de las tasas individuales son Wilson 95%. McNemar es binomial exacto y la columna Holm aplica la corrección a las seis comparaciones RL-heurístico reportadas.

| Terreno | RL éxito | IC95% RL | HEU éxito | IC95% HEU | Delta RL-HEU (pp) | p McNemar | p Holm |
|---|---:|---:|---:|---:|---:|---:|---:|
| V3_F3_02 | 87/100 | [79.0, 92.2] | 89/100 | [81.4, 93.7] | -2 | 0.814529 | 1.000000 |
| BigRock | 86/100 | [77.9, 91.5] | 83/100 | [74.5, 89.1] | +3 | 0.647606 | 1.000000 |
| HardTerrain | 95/100 | [88.8, 97.8] | 90/100 | [82.6, 94.5] | +5 | 0.301758 | 0.905273 |
| BumpyGround | 31/100 | [22.8, 40.6] | 70/100 | [60.4, 78.1] | -39 | 7.597e-09 | 4.558e-08 |
| Complete | 19/100 | [12.5, 27.8] | 49/100 | [39.4, 58.7] | -30 | 2.272e-07 | 1.136e-06 |
| DeepHoles | 17/100 | [10.9, 25.5] | 42/100 | [32.8, 51.8] | -25 | 4.126e-05 | 1.650e-04 |

Conclusión que sí queda respaldada: bajo esta política entrenada y estos escenarios de evaluación, no se observa diferencia estadísticamente detectable en V3_F3_02, BigRock o HardTerrain; sí aparece una degradación grande de la tasa de éxito del RL respecto al heurístico en BumpyGround, Complete y DeepHoles.

La inferencia se refiere a la política PPO evaluada, no a PPO/RL como clase de algoritmos, porque existe una única realización de entrenamiento final.

## 5. Fallos observados por terreno

| Terreno | RL | HEU |
|---|---|---|
| V3_F3_02 | SUCCESS 87, STUCK 8, COLLISION 5 | SUCCESS 89, STUCK 10, COLLISION 1 |
| BigRock | SUCCESS 86, COLLISION 9, STUCK 5 | SUCCESS 83, STUCK 15, COLLISION 2 |
| HardTerrain | SUCCESS 95, STUCK 4, COLLISION 1 | SUCCESS 90, STUCK 8, COLLISION 2 |
| BumpyGround | SUCCESS 31, STUCK 46, FALL 16, COLLISION 7 | SUCCESS 70, FALL 15, STUCK 10, COLLISION 5 |
| Complete | SUCCESS 19, FALL 35, STUCK 33, COLLISION 13 | SUCCESS 49, FALL 34, COLLISION 9, STUCK 8 |
| DeepHoles | SUCCESS 17, FALL 43, STUCK 35, COLLISION 5 | SUCCESS 42, FALL 47, STUCK 10, COLLISION 1 |

Este desglose es más informativo para la discusión que multiplicar contrastes estadísticos por categoría de fallo.

## 6. `Complete`: bruto frente al filtrado histórico

El script OE8 elimina cualquier episodio/seed en el que RL o HEU presenta `FALL` en <=50 pasos. El criterio excluye 37/100 pares.

- Bruto: RL 19/100 (19%) frente a HEU 49/100 (49%); Delta=-30 pp; McNemar p=2.272e-07.
- Filtrado: RL 18/63 (28.6%) frente a HEU 48/63 (76.2%); Delta=-47.62 pp; McNemar p=6.938e-08.

El filtrado amplifica fuertemente la diferencia observada. Además, la justificación del script ("fallos de spawn no atribuibles a la política") no puede demostrarse solo con los CSV y el criterio depende del resultado posterior al inicio del episodio. Por ello, no debe usarse como análisis principal.

## 7. Errores confirmados en los scripts históricos

### 7.1 IC de diferencia de proporciones pareadas

`diff_props_paired_ci()` en OE8 y OE9 introduce una división adicional por la raíz de `n`, reduciendo artificialmente el error estándar. Ejemplo: para BumpyGround se publicaba aproximadamente -39 pp con IC [-40.1, -37.9], mientras una aproximación normal pareada correctamente escalada da aproximadamente [-50.4, -27.6].

Los IC antiguos de Delta no deben reutilizarse. Para el pipeline del paper se recomienda un IC bootstrap pareado BCa con resampleo de pares completos y semilla del bootstrap fijada. La aproximación normal corregida puede conservarse como comprobación de sensibilidad, no como fuente final si se elige BCa.

### 7.2 Tamaño de efecto de Wilcoxon

Los scripts calculan `r=|Z|/sqrt(n)` reconstruyendo Z a partir del p-valor bilateral devuelto por `scipy.stats.wilcoxon`. Ese procedimiento no recupera necesariamente el estadístico Z usado por Wilcoxon y produce incluso valores `r>1` (se observó 1.0268 para n=14), lo que prueba que no es un tamaño de efecto válido en esta implementación.

Debe sustituirse por correlación biserial por rangos pareada, calculada directamente a partir de rangos positivos y negativos, siempre dentro de [-1,1].

### 7.3 Multiplicidad en OE9

OE9 ejecuta múltiples contrastes intra-sistema, inter-sistema y análisis "clean" sin una corrección global/familiar equivalente a la de OE8. Para el paper los análisis de perturbación deben etiquetarse como secundarios/exploratorios y definir previamente las familias de hipótesis; Holm es adecuado si se conservan los contrastes inferenciales.

### 7.4 Ejecutabilidad de OE9

`analisis_estadistico_oe9.py` contiene sintaxis de notebook/Colab (`!pip install ...`) y no es un script Python estándar ejecutable directamente. El notebook original puede ejecutarse en Colab, pero para el paper debe reemplazarse por un pipeline Python limpio y reproducible.

## 8. Variables continuas: interpretación correcta

Las comparaciones históricas de `pasos`, `tiempo_s`, `distancia_final_m` y `energia_total` se realizan solo sobre seeds donde ambos sistemas obtienen `SUCCESS`. Deben presentarse como resultados de eficiencia condicionados al éxito común, no como rendimiento global.

Dos correcciones conceptuales son necesarias:

1. `pasos` y `tiempo_s` son prácticamente la misma variable: el Fixed Timestep del proyecto es aproximadamente 0.01 s y los CSV cumplen `tiempo_s ~ pasos*0.01`. No conviene realizar/publicar dos contrastes como si fueran medidas independientes. Conservar `tiempo_s` es suficiente.
2. `energia_total` no mide energía física. El código acumula `abs(leftVel)+abs(rightVel)` en cada paso. Debe denominarse, por ejemplo, `cumulative actuation-effort proxy`; no debe expresarse en J ni interpretarse como consumo energético real.

`distancia_final_m` tiene muy poca capacidad discriminativa en episodios exitosos porque el criterio de éxito se activa a 2 m. Su utilidad es mayor como descriptivo de fallos que como métrica de eficiencia entre éxitos.

## 9. Análisis de sensibilidad/robustez existentes

### Anti-atasco

- BumpyGround, SCI estándar -> SCI200: 31% -> 40%, McNemar exacto p=0.07835. No alcanza 0.05.
- Complete, baseline -> MaxStuck10: 19% -> 24%, McNemar exacto p=0.26685.

Estos resultados apoyan tratar la degradación como algo que no desaparece simplemente al relajar moderadamente los umbrales, pero no prueban causalmente el origen del fallo.

### Fricción/par (OE9)

Tasas observadas:

- RL V3: 87% baseline, 98% alta fricción, 93% par alto.
- RL BumpyGround: 31% baseline, 17% alta fricción, 28% par alto.
- HEU V3: 89% baseline, 92% alta fricción, 89% par alto.
- HEU BumpyGround: 70% baseline, 73% alta fricción, 74% par alto.

Aplicando Holm a los ocho contrastes intra-sistema baseline-vs-perturbación, permanecen significativos los dos cambios de alta fricción en RL: V3 87->98% (p ajustado 0.0078125) y BumpyGround 31->17% (p ajustado aproximadamente 0.0304). Los restantes no son significativos en esa familia.

Debe evitarse interpretar el material `Terrain_Sticky_x15` como un coeficiente de fricción efectivo único del contacto rover-terreno sin justificar la combinación de los PhysicsMaterials de rueda y terreno. Es más seguro describir la perturbación por la configuración de materiales aplicada.

## 10. Seeds y emparejamiento

El código de RL y heurístico genera listas mediante `System.Random(masterSeed)` y ambos usan `masterSeed=12345`, `numSeedsToGenerate=100`.

`SampleScene.unity` conserva dos listas serializadas completas de 100 seeds, una para RL y otra para HEU. Son idénticas elemento a elemento. La misma secuencia aparece serializada para el heurístico en `EvaluationRL.unity`. Empieza por `66747, 70160, 774765, 511139, ...` y termina en `..., 111369, 254993, 463381, 615514`.

El procedimiento de spawn también coincide entre controladores: cada episodio llama primero a `TerrainGenerator4.GenerateTerrain(currentSeed)`, que reinicializa `UnityEngine.Random`, y después usa la misma secuencia de llamadas para orientación inicial y objetivo.

Limitación: los CSV guardan el número de episodio, no el valor de seed, y el estado actual de `EvaluationRL.unity` ya no conserva la lista RL serializada. El emparejamiento queda respaldado por el proyecto y la secuencia conservada, pero el CSV aislado no es autosuficiente. El nuevo manifest del paper debe incluir la lista explícita episodio->seed.

## 11. Equivalencia RL-heurístico

Los prefabs serializados de RL y heurístico comparten los parámetros terminales relevantes:

- successDistance=2 m;
- stuckRadiusThreshold=0.05;
- stuckCheckInterval=100;
- maxStuckPermitido=5;
- maxSpinPermitido=3.

Aunque los defaults actuales de `HuskyAgent2.cs` muestran otros valores, el prefab `Environment.prefab` los sobrescribe con los valores anteriores. Por tanto, para las escenas basadas en ese prefab los defaults del script no son los efectivos.

No obstante, la implementación no es literalmente idéntica: el heurístico incorpora un `OnCollisionStay` de respaldo que RL no tiene. No aparece `COLLISION_STAY` en los seis datasets primarios, por lo que no tuvo efecto registrado, pero el paper no debe afirmar identidad de código terminal.

La equivalencia perceptiva tampoco debe formularse como identidad de observaciones. RL dispone de dos `RayPerceptionSensorComponent3D` (frontal y suelo), además de observaciones vectoriales. El heurístico replica la geometría frontal mediante SphereCasts (8 m, radio 0.25 m, 7 rayos por dirección, +/-70 grados) y usa rumbo/tilt directamente. Es defendible hablar de plataforma y geometría frontal comparables; no de vectores perceptivos idénticos.

## 12. Versiones y trazabilidad del modelo

- Unity: 6000.3.6f1.
- ML-Agents Unity package registrado por timers: 4.0.1.
- ML-Agents Python registrado en los training logs finales: 1.2.0.dev0.
- PyTorch registrado: 2.5.1+cu121.
- Fixed Timestep: aproximadamente 0.01 s.
- Escena de entrenamiento: 9 instancias de `Environment.prefab`; el timer de entrenamiento confirma 9 agentes inicializados.

Los ONNX de `Assets/ModelosIA/Usados Actualmente/V3_F1_02`, `V3_F2_02` y `V3_F3_02` son idénticos byte a byte a sus correspondientes ONNX finales bajo `results/`. El modelo usado por la escena de evaluación RL referencia `V3_F3_02`.

La continuidad exacta del currículo final no puede reconstruirse de forma concluyente solo desde `configuration.yaml`, porque algunos runs fueron reanudados y esos archivos reflejan la invocación final. El repositorio sí contiene numerosas evidencias de transferencias explícitas `--initialize-from` entre fases, pero el timer conservado de `HuskyV3_F3_02` registra la última invocación como `--resume`. El paper debe documentar la genealogía exacta del modelo final a partir de los comandos/notas originales si se dispone de ellos, y no inferirla de un único `configuration.yaml` final.

## 13. Reproducibilidad del snapshot

El snapshot no representa simultáneamente todas las condiciones con las que se generaron los CSV. Ejemplo: el código actual del heurístico tiene `forceLimit=2000` y deja 1000 comentado, mientras la escena conserva nombres asociados a la prueba `FL2000_BumpyGround`. Los CSV baseline fueron generados antes de esos cambios manuales.

Por ello, el paper debe crear un manifest explícito de cada dataset con: sistema, terreno, modelo, lista de seeds, material físico, force limit, umbrales terminales y nombre/hash del CSV. La configuración actual del proyecto no debe usarse por sí sola como prueba de que todas las condiciones históricas tuvieron simultáneamente esos valores.

Además, `Packages/manifest.json` referencia ML-Agents y URDF Importer mediante rutas locales absolutas de Windows. El proyecto tal como está no es portable a otro equipo sin resolver esas dependencias. Esto es relevante si se promete liberación reproducible del entorno.

## 14. Terrenos de entrenamiento y test

El proyecto separa assets de terreno bajo `Terrain_Families_Train/` y `Terrain_Families_Test/`. Los cinco tests tienen configuraciones propias para BigRock, BumpyGround, Complete, DeepHoles y HardTerrain. Esto respalda la separación conceptual train/test, aunque para demostrar formalmente que cada familia de test no fue usada durante entrenamiento también debe reconstruirse la genealogía de escenas/configuraciones de entrenamiento del modelo final.

## 15. Qué se puede congelar ya y qué no

### Puede congelarse

- Los 100 pares brutos por terreno como unidad de evaluación condicionada a la política final.
- Las tasas de éxito primarias y Wilson IC95% de la tabla de la sección 4.
- Los p-valores exactos de McNemar y su corrección de Holm de la sección 4.
- Las distribuciones de modos de fallo de la sección 5.
- La decisión de usar Complete bruto como primario.
- La identidad hash de los modelos finales y el uso de V3_F3_02 en evaluación.
- La existencia de una lista compartida de 100 seeds y su secuencia conservada.

### Aún no debe congelarse

- Los IC históricos de Delta de proporciones.
- Los `r` históricos de Wilcoxon.
- Cualquier cifra tomada de tablas de la memoria en vez de regenerada desde CSV.
- La interpretación de `energia_total` como energía física.
- Los resultados filtrados de Complete como evidencia principal.
- La afirmación de igualdad perceptiva/terminal absoluta entre controladores.
- La genealogía exacta del currículo final hasta reconstruirla de forma explícita.

## 16. Pipeline recomendado para el siguiente paso

Crear un `paper_analysis.py` independiente de los scripts OE8/OE9 que:

1. cargue fuentes mediante un manifest, no mediante copias manuales al directorio de trabajo;
2. valide esquema, hashes, episodios 1..100 y alineación;
3. incorpore `episode_seed` mediante la lista serializada conservada;
4. genere la tabla primaria de tasas, Wilson, Delta, McNemar exacto y Holm;
5. calcule IC de Delta mediante bootstrap pareado BCa reproducible;
6. trate Complete bruto como primario y el filtrado como sensibilidad;
7. genere modos de fallo descriptivos;
8. limite las continuas inferenciales a resultados condicionados al éxito común, evitando duplicar pasos/tiempo y usando rank-biserial en lugar del `r` antiguo;
9. renombre `energia_total` como proxy de esfuerzo de actuación;
10. separe OE9 y variantes anti-atasco como sensibilidad/exploratorio y aplique multiplicidad por familia;
11. exporte CSV/JSON finales que sean la única fuente numérica de tablas, figuras y Results del paper.

Estado de la auditoría: **base empírica primaria aceptable con correcciones obligatorias del pipeline y mejoras de trazabilidad antes de congelar el paquete estadístico del manuscrito**.
