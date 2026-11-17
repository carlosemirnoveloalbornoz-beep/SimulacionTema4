import random
import simpy

# ---------- Datos del documento (se pueden cambiar) ----------
HORA_PICO = 45          # minuto 45 = 5:45 p. m. (empieza la hora pico)
HORA_FUNCION = 60       # minuto 60 = 6:00 p. m. (empieza la función)
LLEGADA_NORMAL = 3      # antes de las 5:45 llega 1 cliente cada ~3 min
LLEGADA_PICO = 1.5      # en hora pico llegan más seguido (supuesto mío)
TAQUILLA_MIN = 2        # atención en taquilla: de 2 a 3 minutos
TAQUILLA_MAX = 3
DULCERIA_PROMEDIO = 5   # atención en dulcería: unos 5 minutos
CLIENTES_DULCERIA = 7   # 7 de cada 10 clientes pasan a dulcería (supuesto mío)

# Aquí se guardan los tiempos de espera de cada cliente
esperas_taquilla = []
esperas_dulceria = []
filas_taquilla = []   # cuántas personas había en la fila cuando llegó cada cliente


def cliente(env, taquilla, dulceria):
    """Lo que hace un cliente: taquilla y luego dulcería."""
    # --- Taquilla ---
    llegada = env.now
    filas_taquilla.append(len(taquilla.queue))        # personas esperando delante
    with taquilla.request() as turno:
        yield turno                                   # espera su turno
        esperas_taquilla.append(env.now - llegada)    # guardamos cuánto esperó
        yield env.timeout(random.uniform(TAQUILLA_MIN, TAQUILLA_MAX))

    # --- Dulcería (solo algunos clientes) ---
    if random.randint(1, 10) <= CLIENTES_DULCERIA:
        llegada = env.now
        with dulceria.request() as turno:
            yield turno
            esperas_dulceria.append(env.now - llegada)
            yield env.timeout(random.expovariate(1 / DULCERIA_PROMEDIO))


def llegada_de_clientes(env, taquilla, dulceria):
    """Crea clientes uno por uno hasta que empieza la función."""
    while env.now < HORA_FUNCION:
        env.process(cliente(env, taquilla, dulceria))
        if env.now < HORA_PICO:
            espera = random.expovariate(1 / LLEGADA_NORMAL)  # llegadas al azar
        else:
            espera = random.expovariate(1 / LLEGADA_PICO)
        yield env.timeout(espera)


def simular(num_taquillas, num_dulceria):
    """Corre una simulación completa y regresa los resultados."""
    esperas_taquilla.clear()
    esperas_dulceria.clear()
    filas_taquilla.clear()

    env = simpy.Environment()
    taquilla = simpy.Resource(env, capacity=num_taquillas)
    dulceria = simpy.Resource(env, capacity=num_dulceria)

    env.process(llegada_de_clientes(env, taquilla, dulceria))
    env.run()   # corre hasta que todos los clientes terminan

    promedio_t = sum(esperas_taquilla) / len(esperas_taquilla)
    maximo_t = max(esperas_taquilla)
    if esperas_dulceria:
        promedio_d = sum(esperas_dulceria) / len(esperas_dulceria)
    else:
        promedio_d = 0
    fila_prom = sum(filas_taquilla) / len(filas_taquilla)
    fila_max = max(filas_taquilla)
    return len(esperas_taquilla), promedio_t, maximo_t, promedio_d, fila_prom, fila_max


# ---------- Programa principal ----------
escenarios = [
    ("A (actual: 1 taquilla)", 1, 3),
    ("B (2 taquillas)", 2, 3),
    ("C (2 taquillas, 2 en dulcería)", 2, 2),
]

REPETICIONES = 30   # se repite varias veces porque todo es aleatorio

resumen = []   # aquí guardamos los resultados para comparar al final

for nombre, n_taquillas, n_dulceria in escenarios:
    suma_prom_t = 0
    suma_max_t = 0
    suma_prom_d = 0
    suma_fila_prom = 0
    suma_fila_max = 0
    clientes = 0
    for i in range(REPETICIONES):
        random.seed(i)   # misma semilla para comparar justo los escenarios
        c, prom_t, max_t, prom_d, fila_prom, fila_max = simular(n_taquillas, n_dulceria)
        clientes += c
        suma_prom_t += prom_t
        suma_max_t += max_t
        suma_prom_d += prom_d
        suma_fila_prom += fila_prom
        suma_fila_max += fila_max

    espera_t = suma_prom_t / REPETICIONES
    espera_d = suma_prom_d / REPETICIONES
    resumen.append((nombre, espera_t + espera_d))

    print("Escenario", nombre)
    print("  Clientes atendidos (promedio):  ", round(clientes / REPETICIONES))
    print("  Espera promedio en taquilla:    ", round(espera_t, 1), "min")
    print("  Espera máxima en taquilla:      ", round(suma_max_t / REPETICIONES, 1), "min")
    print("  Fila promedio en taquilla:      ", round(suma_fila_prom / REPETICIONES), "personas")
    print("  Fila máxima en taquilla:        ", round(suma_fila_max / REPETICIONES), "personas")
    print("  Espera promedio en dulcería:    ", round(espera_d, 1), "min")
    print()

# ---------- Comparación final ----------
# Se suma la espera en taquilla + dulcería y gana el escenario con menos espera
print("COMPARACIÓN (espera total promedio por cliente):")
mejor = resumen[0]
for nombre, total in resumen:
    print("  Escenario", nombre, "->", round(total, 1), "min")
    if total < mejor[1]:
        mejor = (nombre, total)
print("Mejor escenario:", mejor[0])