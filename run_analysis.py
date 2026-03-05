import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Carregar a base de dados
df = pd.read_csv('base_motos_VIP_mestre.csv')
print("head():\n", df.head())

print("\ndescribe():\n", df.describe())

numeric_df = df.select_dtypes(include=['number'])
corr = numeric_df.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
plt.title('Mapa de Calor - Correlação entre Variáveis Numéricas')
plt.savefig('heatmap_motos_VIP.png')

plt.figure(figsize=(10, 5))
sns.histplot(df['preco_limpo'], bins=50, kde=True, color='blue')
plt.title('Distribuição de Preço das Motos')
plt.xlabel('Preço')
plt.ylabel('Frequência')
plt.savefig('distribuicao_preco_motos_VIP.png')

preco_zero = df[df['eh_zero_km'] == True]['preco_limpo'].dropna()
preco_usada = df[df['eh_zero_km'] == False]['preco_limpo'].dropna()

t_stat, p_value = stats.ttest_ind(preco_zero, preco_usada, equal_var=False)
print(f'\nT-statistic: {t_stat:.4f}')
print(f'P-value: {p_value:.4e}')

if p_value < 0.05:
    print('Rejeitamos a hipótese nula. Há uma diferença significativa de preço entre motos Zero KM e Usadas.')
else:
    print('Não rejeitamos a hipótese nula. Não há evidência de diferença significativa de preço.')
