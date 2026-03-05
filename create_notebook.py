import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Análise Ciência de Dados - Base de Motos VIP Mestre\n",
    "Este notebook apresenta uma análise exploratória de dados (EDA) e testes estatísticos para a base `base_motos_VIP_mestre.csv`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from scipy import stats\n",
    "\n",
    "# Carregar a base de dados\n",
    "df = pd.read_csv('base_motos_VIP_mestre.csv')\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Estatísticas Descritivas Básicas\n",
    "Visualizando um resumo das variáveis numéricas."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "df.describe()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Mapa de Calor (Correlação)\n",
    "Verificando a correlação linear entre as variáveis numéricas (como ano e preço)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "numeric_df = df.select_dtypes(include=['number'])\n",
    "corr = numeric_df.corr()\n",
    "\n",
    "plt.figure(figsize=(8, 6))\n",
    "sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)\n",
    "plt.title('Mapa de Calor - Correlação entre Variáveis Numéricas')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Distribuição de Preço\n",
    "Como se comportam os preços nesta base?"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "plt.figure(figsize=(10, 5))\n",
    "sns.histplot(df['preco_limpo'], bins=50, kde=True, color='blue')\n",
    "plt.title('Distribuição de Preço das Motos')\n",
    "plt.xlabel('Preço')\n",
    "plt.ylabel('Frequência')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. Teste Estatístico (T-Test)\n",
    "Existe uma diferença estatisticamente significativa nos preços entre motos Zero km e motos Usadas?"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "preco_zero = df[df['eh_zero_km'] == True]['preco_limpo'].dropna()\n",
    "preco_usada = df[df['eh_zero_km'] == False]['preco_limpo'].dropna()\n",
    "\n",
    "t_stat, p_value = stats.ttest_ind(preco_zero, preco_usada, equal_var=False)\n",
    "print(f'T-statistic: {t_stat:.4f}')\n",
    "print(f'P-value: {p_value:.4e}')\n",
    "\n",
    "if p_value < 0.05:\n",
    "    print('Rejeitamos a hipótese nula. Há uma diferença significativa de preço entre motos Zero KM e Usadas.')\n",
    "else:\n",
    "    print('Não rejeitamos a hipótese nula. Não há evidência de diferença significativa de preço.')"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
with open('analise_cientista_dados.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)
print("Notebook analise_cientista_dados.ipynb gerado com sucesso.")
