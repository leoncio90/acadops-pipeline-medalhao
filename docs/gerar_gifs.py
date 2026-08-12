import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

FONTE = 'Liberation Sans'
plt.rcParams['font.family'] = FONTE

FUNDO = '#FBFAF8'
TINTA = '#1F2328'
CINZA = '#6B7280'
BRONZE = '#A9714B'
SILVER = '#7C8894'
GOLD = '#C39B2E'
ORIGEM = '#3F4A56'
ALERTA = '#B4453C'
APAGADO = '#DEDAD4'

os.makedirs('/tmp/frames_fluxo', exist_ok=True)
os.makedirs('/tmp/frames_triagem', exist_ok=True)


def suavizar(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ============================================================ GIF 1: o fluxo
ESTAGIOS = [
    {'nome': 'ORIGEM', 'cor': ORIGEM, 'x': 0.55, 'w': 2.1,
     'linhas': ['CSV de entrada', '', '4 arquivos'],
     'legenda': '4 arquivos CSV  ·  44 linhas na entrada'},
    {'nome': 'BRONZE', 'cor': BRONZE, 'x': 3.05, 'w': 2.55,
     'linhas': ['UTF-8 + correção', 'de mojibake', 'partição por', 'ingestion_date'],
     'legenda': 'Nutrição deixa de virar NutriÃ§Ã£o  ·  partição por data de ingestão'},
    {'nome': 'SILVER', 'cor': SILVER, 'x': 6.0, 'w': 2.55,
     'linhas': ['tipos, normalização', 'de texto, dedup', 'e validação', 'de e-mail'],
     'legenda': 'Data inválida, ID duplicado e e-mail malformado saem do fluxo'},
    {'nome': 'GOLD', 'cor': GOLD, 'x': 8.95, 'w': 2.5,
     'linhas': ['regra de negócio', 'e entregável', 'JSON / CSV', 'utf-8-sig'],
     'legenda': '41 ações geradas em acoes_provas.json'}
]

Y = 2.30
H = 2.40
FRAMES_FLUXO = 96


def frame_fluxo(i):
    fig, ax = plt.subplots(figsize=(12, 6.28), dpi=100)
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.28)
    ax.axis('off')

    ax.text(0.55, 5.84, 'Arquitetura Medalhão', fontsize=25, fontweight='bold', color=TINTA, va='center')
    ax.text(0.55, 5.36, 'Cada camada resolve um tipo de problema. E nada é descartado em silêncio.',
            fontsize=12.5, color=CINZA, va='center')

    # cada estágio ganha 20 frames: 12 processando, 8 em trânsito para o próximo
    ativo = min(i // 24, 3)
    t_local = (i % 24) / 24.0
    transito = t_local > 0.62 and ativo < 3

    for k, e in enumerate(ESTAGIOS):
        aceso = k <= ativo
        cor = e['cor'] if aceso else APAGADO
        cor_texto = 'white' if aceso else '#A8A29A'
        ax.add_patch(FancyBboxPatch((e['x'], Y), e['w'], H, boxstyle="round,pad=0,rounding_size=0.12",
                                    linewidth=0, facecolor=cor, zorder=2))
        ax.text(e['x'] + e['w'] / 2, Y + H - 0.42, e['nome'], ha='center', va='center', color=cor_texto,
                fontsize=15, fontweight='bold', zorder=3)
        for j, linha in enumerate(e['linhas']):
            ax.text(e['x'] + e['w'] / 2, Y + H - 0.85 - j * 0.34, linha, ha='center', va='center',
                    color=cor_texto, fontsize=10.5, alpha=0.92, zorder=3)

    for k in range(3):
        x1 = ESTAGIOS[k]['x'] + ESTAGIOS[k]['w']
        x2 = ESTAGIOS[k + 1]['x']
        cor_seta = CINZA if k <= ativo else '#D8D3CC'
        ax.add_patch(FancyArrowPatch((x1 + 0.05, Y + H / 2), (x2 - 0.05, Y + H / 2), arrowstyle='-|>',
                                     mutation_scale=18, linewidth=1.8, color=cor_seta, zorder=1))

    # o lote de dados em trânsito entre dois estágios
    if transito:
        avanco = suavizar((t_local - 0.62) / 0.38)
        x1 = ESTAGIOS[ativo]['x'] + ESTAGIOS[ativo]['w']
        x2 = ESTAGIOS[ativo + 1]['x']
        px = x1 + (x2 - x1) * avanco
        ax.add_patch(FancyBboxPatch((px - 0.12, Y + H / 2 - 0.12), 0.24, 0.24,
                                    boxstyle="round,pad=0,rounding_size=0.06", linewidth=0,
                                    facecolor=ESTAGIOS[ativo + 1]['cor'], zorder=4))

    # ramo da quarentena: só existe a partir da Silver
    if ativo >= 2:
        cor_ramo = ALERTA
        alpha_ramo = 1.0 if ativo > 2 else suavizar(t_local / 0.55)
        ax.add_patch(FancyArrowPatch((7.27, Y - 0.06), (7.27, 1.42), arrowstyle='-|>', mutation_scale=18,
                                     linewidth=1.8, color=cor_ramo, linestyle=(0, (4, 2.5)),
                                     alpha=alpha_ramo, zorder=1))
        ax.text(7.42, 1.62, 'data/rejected/', fontsize=12, fontweight='bold', color=ALERTA,
                va='center', alpha=alpha_ramo)
        ax.text(7.42, 1.24, '3 registros + motivo_rejeicao', fontsize=10.5, color=CINZA,
                va='center', alpha=alpha_ramo)

        # os três registros rejeitados caindo para a quarentena
        if ativo == 2:
            for n in range(3):
                atraso = 0.12 + n * 0.13
                if t_local > atraso:
                    queda = suavizar((t_local - atraso) / 0.4)
                    ax.add_patch(plt.Circle((7.27, Y - 0.06 - (Y - 1.5) * queda), 0.075,
                                            color=ALERTA, zorder=4))

    # faixa do log, preenchida quando o pipeline conclui
    ax.add_patch(FancyBboxPatch((0.55, 0.32), 10.9, 0.62, boxstyle="round,pad=0,rounding_size=0.1",
                                linewidth=1.2, edgecolor='#DDD9D2', facecolor='white', zorder=2))
    if ativo == 3:
        texto_log = 'log_execucao.csv   ·   run_id da4b6a78   ·   entrada 44   ·   saída 41   ·   rejeitadas 3'
        cor_log = TINTA
    else:
        texto_log = 'log_execucao.csv   ·   run_id   ·   linhas_entrada   ·   linhas_saida   ·   linhas_rejeitadas'
        cor_log = '#9CA3AF'
    ax.text(6.0, 0.63, texto_log, ha='center', va='center', fontsize=11.5, color=cor_log, zorder=3)

    # legenda do estágio corrente
    ax.text(0.55, 4.90, ESTAGIOS[ativo]['legenda'], fontsize=12.5, color=ESTAGIOS[ativo]['cor'],
            fontweight='bold', va='center')

    fig.savefig(f'/tmp/frames_fluxo/f{i:03d}.png', facecolor=FUNDO, bbox_inches='tight', pad_inches=0.25)
    plt.close(fig)


for i in range(FRAMES_FLUXO):
    frame_fluxo(i)


# ============================================================ GIF 2: antes e depois
equipes = ['Suporte N1\n(sem equipe)', 'Infraestrutura', 'Sistemas\nAcadêmicos',
           'Business\nIntelligence', 'Sistemas\nInternos', 'Equipe AVA']
antes = np.array([13, 0, 1, 6, 14, 26], dtype=float)
depois = np.array([0, 6, 1, 6, 14, 33], dtype=float)

FRAMES_TRIAGEM = 78


def frame_triagem(i):
    # 18 frames parado no "antes", 30 de transição, 30 parado no "depois"
    if i < 18:
        p = 0.0
    elif i < 48:
        p = suavizar((i - 18) / 30.0)
    else:
        p = 1.0

    valores = antes + (depois - antes) * p

    fig, ax = plt.subplots(figsize=(12, 6.28), dpi=100)
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)

    y = np.arange(len(equipes))
    cor_barra = [(1 - p) * np.array([0.788, 0.796, 0.808]) + p * np.array([0.765, 0.608, 0.180])]
    ax.barh(y, valores, 0.5, color=cor_barra[0], zorder=2)

    for k, v in enumerate(valores):
        ax.text(v + 0.4, k, f'{int(round(v))}', va='center', fontsize=12,
                fontweight='bold' if p > 0.5 else 'normal', color=TINTA if p > 0.5 else CINZA)

    ax.set_yticks(y)
    ax.set_yticklabels(equipes, fontsize=11.5, color=TINTA)
    ax.set_xlim(0, 38)
    ax.set_xticks([])
    ax.tick_params(axis='y', length=0)
    for lado in ['top', 'right', 'bottom', 'left']:
        ax.spines[lado].set_visible(False)

    ax.set_title('Triagem de 60 chamados: distribuição por equipe',
                 fontsize=21, fontweight='bold', color=TINTA, loc='left', pad=34)

    rotulo = 'antes da correção' if p < 0.5 else 'depois da correção'
    cor_rotulo = CINZA if p < 0.5 else GOLD
    ax.text(0, 1.055, rotulo, transform=ax.transAxes, fontsize=14, fontweight='bold',
            color=cor_rotulo, va='center')

    if p >= 1.0:
        ax.text(1.0, 1.055, '13 chamados sem equipe  →  0', transform=ax.transAxes, fontsize=13,
                color=TINTA, va='center', ha='right')

    fig.savefig(f'/tmp/frames_triagem/f{i:03d}.png', facecolor=FUNDO, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)


for i in range(FRAMES_TRIAGEM):
    frame_triagem(i)

print('frames ok')
