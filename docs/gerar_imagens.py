import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

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


def caixa(ax, x, y, w, h, cor, titulo, linhas, cor_texto='white'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                linewidth=0, facecolor=cor, zorder=2))
    ax.text(x + w / 2, y + h - 0.42, titulo, ha='center', va='center', color=cor_texto,
            fontsize=15, fontweight='bold', zorder=3)
    for i, linha in enumerate(linhas):
        ax.text(x + w / 2, y + h - 0.85 - i * 0.34, linha, ha='center', va='center',
                color=cor_texto, fontsize=10.5, alpha=0.92, zorder=3)


def seta(ax, x1, y1, x2, y2, cor=CINZA, estilo='-'):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=18,
                                 linewidth=1.8, color=cor, linestyle=estilo, zorder=1,
                                 shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- imagem 1
fig, ax = plt.subplots(figsize=(12, 6.28), dpi=200)
fig.patch.set_facecolor(FUNDO)
ax.set_facecolor(FUNDO)
ax.set_xlim(0, 12)
ax.set_ylim(0, 6.28)
ax.axis('off')

ax.text(0.55, 5.78, 'Arquitetura Medalhão', fontsize=25, fontweight='bold', color=TINTA, va='center')
ax.text(0.55, 5.30, 'Cada camada resolve um tipo de problema. E nada é descartado em silêncio.',
        fontsize=12.5, color=CINZA, va='center')

Y = 2.30
H = 2.40
caixa(ax, 0.55, Y, 2.1, H, ORIGEM, 'ORIGEM', ['CSV de entrada', '', '4 arquivos'])
caixa(ax, 3.05, Y, 2.55, H, BRONZE, 'BRONZE', ['UTF-8 + correção', 'de mojibake', 'partição por',
                                               'ingestion_date'])
caixa(ax, 6.0, Y, 2.55, H, SILVER, 'SILVER', ['tipos, normalização', 'de texto, dedup', 'e validação',
                                              'de e-mail'])
caixa(ax, 8.95, Y, 2.5, H, GOLD, 'GOLD', ['regra de negócio', 'e entregável', 'JSON / CSV',
                                          'utf-8-sig'])

for x1, x2 in [(2.65, 3.05), (5.6, 6.0), (8.55, 8.95)]:
    seta(ax, x1, Y + H / 2, x2, Y + H / 2)

# ramo da quarentena, saindo da Silver
seta(ax, 7.27, Y - 0.06, 7.27, 1.42, cor=ALERTA, estilo=(0, (4, 2.5)))
ax.text(7.42, 1.62, 'data/rejected/', fontsize=12, fontweight='bold', color=ALERTA, va='center')
ax.text(7.42, 1.24, 'registro rejeitado + motivo_rejeicao', fontsize=10.5, color=CINZA, va='center')

# rodapé com o log
ax.add_patch(FancyBboxPatch((0.55, 0.32), 10.9, 0.62, boxstyle="round,pad=0,rounding_size=0.1",
                            linewidth=1.2, edgecolor='#DDD9D2', facecolor='white', zorder=2))
ax.text(6.0, 0.63, 'log_execucao.csv   ·   run_id   ·   linhas_entrada   ·   linhas_saida   ·   linhas_rejeitadas',
        ha='center', va='center', fontsize=11.5, color=TINTA, zorder=3)

fig.savefig('docs/arquitetura_medalhao.png', facecolor=FUNDO, bbox_inches='tight',
            pad_inches=0.25)
plt.close(fig)


# ---------------------------------------------------------------- imagem 2
equipes = ['Suporte N1\n(sem equipe)', 'Infraestrutura', 'Sistemas\nAcadêmicos',
           'Business\nIntelligence', 'Sistemas\nInternos', 'Equipe AVA']
antes = [13, 0, 1, 6, 14, 26]
depois = [0, 6, 1, 6, 14, 33]

fig, ax = plt.subplots(figsize=(12, 6.28), dpi=200)
fig.patch.set_facecolor(FUNDO)
ax.set_facecolor(FUNDO)

y = np.arange(len(equipes))
alt = 0.36
ax.barh(y + alt / 2 + 0.02, antes, alt, label='antes da correção', color='#C9CBCE', zorder=2)
ax.barh(y - alt / 2 - 0.02, depois, alt, label='depois', color=GOLD, zorder=2)

for i, (a, d) in enumerate(zip(antes, depois)):
    ax.text(a + 0.4, i + alt / 2 + 0.02, str(a), va='center', fontsize=11, color=CINZA)
    ax.text(d + 0.4, i - alt / 2 - 0.02, str(d), va='center', fontsize=11, fontweight='bold', color=TINTA)

ax.set_yticks(y)
ax.set_yticklabels(equipes, fontsize=11.5, color=TINTA)
ax.set_xlim(0, 38)
ax.set_xticks([])
ax.tick_params(axis='y', length=0)
for lado in ['top', 'right', 'bottom', 'left']:
    ax.spines[lado].set_visible(False)

ax.set_title('Triagem de 60 chamados: distribuição por equipe',
             fontsize=21, fontweight='bold', color=TINTA, loc='left', pad=34)
ax.text(0, 1.055, '13 chamados caíam no suporte genérico por incompatibilidade entre a regra e o texto normalizado. Depois do ajuste: nenhum.',
        transform=ax.transAxes, fontsize=12, color=CINZA, va='center')
ax.legend(loc='lower right', frameon=False, fontsize=11.5)

fig.savefig('docs/triagem_antes_depois.png', facecolor=FUNDO, bbox_inches='tight',
            pad_inches=0.3)
plt.close(fig)

print('ok')
