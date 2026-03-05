import nbformat as nbf

# Load the notebook
notebook_path = 'analise_cientista_dados.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Markdown cell
markdown_cell = nbf.v4.new_markdown_cell("""## 5. ANOVA no Preço: Comparando as 5 Marcas Mais Populares
Neste cenário, estamos verificando se existe uma diferença estatisticamente significativa no preço cobrado entre as 5 marcas com maior volume de motos na base. Usamos o teste ANOVA para comparar mais de duas amostras (grupos).""")

# Code cell
code_cell = nbf.v4.new_code_cell("""top_5_marcas = df['nome_marca'].value_counts().head(5).index
df_top5 = df[df['nome_marca'].isin(top_5_marcas)]

plt.figure(figsize=(12, 6))
sns.boxplot(x='nome_marca', y='preco_limpo', data=df_top5, palette='Set2')
plt.title('Dispersão do Preço para as 5 Marcas Mais Frequentes')
plt.ylabel('Preço Limpo')
plt.xlabel('Marca')
plt.show()

# Agrupando os preços por marca
grupos_de_preco = [df_top5[df_top5['nome_marca'] == marca]['preco_limpo'].dropna() for marca in top_5_marcas]

f_stat, p_value_anova = stats.f_oneway(*grupos_de_preco)
print(f'F-statistic: {f_stat:.4f}')
print(f'P-value: {p_value_anova:.4e}')

if p_value_anova < 0.05:
    print('Veredito: Rejeitamos a hipótese nula. Há diferença significativa de preço entre essas marcas.')
else:
    print('Veredito: Falhamos em rejeitar a hipótese nula. As marcas operam sob a mesma média de preço.')""")

# Append to notebook
nb.cells.append(markdown_cell)
nb.cells.append(code_cell)

# Save the notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
