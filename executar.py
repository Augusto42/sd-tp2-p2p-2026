"""Um terminal: demonstração ou bateria replicável; encerra todos os peers ao fim."""
import argparse
import contextlib
import csv
from datetime import datetime
import io
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tests'))
from integration import run_case, run_failure


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf8')


def battery(repetitions, seed):
    if repetitions < 2:
        raise ValueError('Use pelo menos duas repetições para calcular desvio-padrão amostral.')
    out = ROOT / 'resultados'
    # Uma geração determinística por tamanho: repetições usam os mesmos bytes.
    configurations = [(n, b, size) for size in [10240, 20480, 1048576, 5242880, 10485760, 20971520]
                      for b in [1024, 4096] for n in [2, 4]]
    raw = []
    for rep in range(1, repetitions + 1):
        order = configurations.copy()
        random.Random(seed + rep).shuffle(order)
        for n, b, size in order:
            name = f'medicoes/seed{seed}_r{rep:02d}_n{n}_b{b}_s{size}'
            with contextlib.redirect_stdout(io.StringIO()):
                row = run_case(size, b, n, name, random_seed=seed + size)
            row.update(repetition=rep, input_seed=seed + size)
            # Compartilha o mesmo manifesto entre repetições, sem perder os logs.
            case = out / name
            original = case / 'metadados.json'
            common = out / 'entradas' / f'seed{seed}_s{size}_b{b}.json'
            common.parent.mkdir(parents=True, exist_ok=True)
            if common.exists():
                if common.read_bytes() != original.read_bytes():
                    raise ValueError('Manifesto divergiu: use uma pasta limpa ao trocar a semente.')
            else:
                common.write_bytes(original.read_bytes())
            original.unlink()
            row['metadata_path'] = str(common.relative_to(ROOT))
            (case / 'metadados_ref.txt').write_text(row['metadata_path'] + '\n')
            write_json(case / 'verificacao.json', row)
            raw.append(row)
            write_json(out / 'medicoes.json', raw)
            print(f'[{len(raw):03d}/{24*repetitions}] repetição {rep}: {n} peers, bloco {b}, arquivo {size} bytes — {row["seconds"]:.4f} s — PASS', flush=True)
    summary = []
    for n, b, size in configurations:
        group = [r for r in raw if (r['peers'], r['block_bytes'], r['size_bytes']) == (n, b, size)]
        times = [r['seconds'] for r in group]
        summary.append(dict(peers=n, block_bytes=b, size_bytes=size, repetitions=len(times),
                            mean_seconds=statistics.mean(times), std_seconds=statistics.stdev(times),
                            min_seconds=min(times), max_seconds=max(times), seconds=times,
                            integrity='PASS', topology='mesh'))
    write_json(out / 'estatisticas.json', summary)
    with (out / 'estatisticas.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader(); writer.writerows(summary)
    extras = []
    jobs = [('compartilhamento_parcial', lambda: run_case(131123, 1024, 4, 'compartilhamento_parcial', delay=.001)),
            ('seeder_tardio', lambda: run_case(65539, 1024, 2, 'seeder_tardio', recovery=True)),
            ('malha_completa', lambda: run_case(1048576, 4096, 4, 'malha_completa')),
            ('queda_temporaria', lambda: run_failure('temporaria')),
            ('queda_permanente', lambda: run_failure('permanente'))]
    jobs.extend((f'queda_aleatoria_{s}', lambda s=s: run_failure('aleatoria', random_seed=s)) for s in range(5))
    for name, run in jobs:
        with contextlib.redirect_stdout(io.StringIO()):
            result = run()
        extras.append(result)
        print(f'{name}: PASS', flush=True)
    write_json(out / 'adicionais.json', extras)
    write_json(out / 'ambiente.json', dict(python=sys.version, platform=platform.platform(),
        date=datetime.now().astimezone().isoformat(), network='TCP loopback, processos independentes',
        repetitions=repetitions, random_seed=seed, order='embaralhada por repetição com seed + repetição',
        input='bytes pseudoaleatórios replicáveis; seed + tamanho; mesmos bytes por tamanho em todas as repetições',
        units='KB/MB interpretados como KiB/MiB', deviation='desvio-padrão amostral, denominador n - 1',
        timing='inicialização até arquivos completos e conexão de cada leecher a todos os vizinhos; inclui logs'))
    write_json(out / 'bateria.json', dict(matrix_cases=len(raw), configurations=24, repetitions=repetitions,
        additional_cases=len(extras), integration_total=len(raw)+len(extras), unit_tests=11, result='PASS'))
    print(f'CONCLUÍDO: {len(raw)+len(extras)} integrações aprovadas; todos os processos encerrados.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--demo', action='store_true', help='Demonstração automática (padrão)')
    mode.add_argument('--testes', action='store_true', help='Unitários + matriz repetida + quedas')
    parser.add_argument('--repeticoes', type=int, default=5)
    parser.add_argument('--seed', type=int, default=2026)
    args = parser.parse_args()
    if args.testes:
        unit = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT/'tests'), '-v'],
                              capture_output=True, text=True)
        (ROOT/'resultados').mkdir(exist_ok=True)
        (ROOT/'resultados/unitarios.txt').write_text(unit.stdout + unit.stderr)
        if unit.returncode:
            print(unit.stdout + unit.stderr); return unit.returncode
        print('11 testes unitários: PASS', flush=True)
        battery(args.repeticoes, args.seed)
    else:
        print('DEMONSTRAÇÃO: 4 processos em malha; inicialização, falha, verificação e encerramento automáticos.', flush=True)
        run_failure('temporaria', demo=True)
        run_failure('aleatoria', demo=True, random_seed=args.seed)
        print('DEMONSTRAÇÃO CONCLUÍDA: todos os peers encerrados.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
