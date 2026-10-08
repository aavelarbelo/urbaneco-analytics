# Medidas e colunas DAX — dashboard UrbanEco

Fórmulas extraídas do relatório Power BI (versão de 7 de outubro de 2026).

- As medidas e colunas originais foram criadas pelo grupo durante o projeto final (junho de 2026).
- As alterações da revisão de outubro de 2026 estão marcadas com **[revisão out/2026]** e incluem comentários na própria fórmula.
- Tabela principal: `Tab_anuncios_imoveis` (um registo por anúncio). As tabelas de apoio (`energy_score`, `medianas_segmento`, `premio_energetico`, `indice_verde_geral`, `indice_verde_rankings`) vêm da base PostgreSQL do grupo.

## Colunas calculadas

### `Tab_anuncios_imoveis[€/m2]`

```dax
Tab_anuncios_imoveis[preco]/Tab_anuncios_imoveis[area_util]
```

### `Tab_anuncios_imoveis[energyscore]`

```dax
RELATED(energy_score[energy_score])
```

### `Tab_anuncios_imoveis[Location Score]`

```dax
RELATED(indice_verde_geral[indice_verde_100])/20
```

### `Tab_anuncios_imoveis[mediana_segmento]`

```dax
RELATED(medianas_segmento[mediana_m2])
```

### `Tab_anuncios_imoveis[Price Score]`

```dax
VAR preco_m2 = Tab_anuncios_imoveis[€/m2]
VAR mediana  = Tab_anuncios_imoveis[mediana_segmento]
VAR desvio   = DIVIDE(preco_m2 - mediana, mediana) * 100
VAR score    = 3 - DIVIDE(desvio, 10)
RETURN
    IF(
        ISBLANK(mediana) || mediana = 0,
        BLANK(),
        MIN(5, MAX(0, score))
    )
```

### `Tab_anuncios_imoveis[EVI]` **[revisão out/2026]**

```dax
-- Índice de Valor Energético (0–100) = (Price Score×0,4 + Energy Score×0,3 + Location Score×0,3)×20
-- Correção (out/2026): fica em branco quando falta uma componente
--   • classe NT (sem certificado) não tem Energy Score → antes contava como 0 (igual à classe G)
--   • segmentos com < 4 anúncios não têm Price Score → antes contava como 0
IF(
    ISBLANK(Tab_anuncios_imoveis[energyscore]) || ISBLANK(Tab_anuncios_imoveis[Price Score]),
    BLANK(),
    ((Tab_anuncios_imoveis[Price Score]*0.4)+(Tab_anuncios_imoveis[energyscore]*0.3)+(Tab_anuncios_imoveis[Location Score]*0.3))*20
)
```

### `Tab_anuncios_imoveis[Link]`

```dax
"Ver anúncio"
```

### `premio_energetico[Classe]`

```dax
IF(
    premio_energetico[classe_energetica] = "A", "B " & UNICHAR(8594) & " A",
    IF(
        premio_energetico[classe_energetica] = "B", "C " & UNICHAR(8594) & " B",
        IF(
            premio_energetico[classe_energetica] = "C", "D " & UNICHAR(8594) & " C",
            IF(
                premio_energetico[classe_energetica] = "D", "E " & UNICHAR(8594) & " D",
                IF(
                    premio_energetico[classe_energetica] = "E", "F " & UNICHAR(8594) & " E",
                    IF(
                        premio_energetico[classe_energetica] = "F", "G " & UNICHAR(8594) & " F",
                        BLANK()
                    )
                )
            )
        )
    )
)
```

### `premio_energetico[ordenação]`

```dax
IF(
    premio_energetico[classe_energetica] = "A",1,
    IF(
        premio_energetico[classe_energetica] = "B",2,
        IF(
            premio_energetico[classe_energetica] = "C", 3,
            IF(
                premio_energetico[classe_energetica] = "D", 4,
                IF(
                    premio_energetico[classe_energetica] = "E", 5,
                    IF(
                        premio_energetico[classe_energetica] = "F", 6,
                        BLANK()
                    )
                )
            )
        )
    )
)
```

## Medidas

### Contagens e eficiência energética

#### `Total_imoveis`

```dax
COUNTROWS(Tab_anuncios_imoveis)
```

#### `Classe_A`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="A")
```

#### `Classe_B`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="B")
```

#### `Classe_C`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="C")
```

#### `Classe_D`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="D")
```

#### `Classe_E`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="E")
```

#### `Classe_F`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="F")
```

#### `Classe_G`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="G")
```

#### `Classe_NT`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]="NT")
```

#### `Class_Eficiente`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica] in {"A","B"})
```

#### `Class_Ineficiente`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica] in {"C","D","E","F","G"})
```

#### `Total_Classificação`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[classe_energetica]<> "NT")
```

#### `Taxa_eficiencia`

```dax
DIVIDE([Class_Eficiente],[Total_Classificação])
```

#### `Total_EVI>50`

```dax
CALCULATE(COUNTROWS(Tab_anuncios_imoveis),Tab_anuncios_imoveis[EVI]>=50)
```

### Preço face ao grupo comparável (página Oportunidades)

#### `Mediana_Grupo`

```dax
CALCULATE(
    MEDIAN(Tab_anuncios_imoveis[€/m2]),
    ALLEXCEPT(
        Tab_anuncios_imoveis,
        Tab_anuncios_imoveis[freguesia],
        Tab_anuncios_imoveis[tipo],
        Tab_anuncios_imoveis[tipologia],
        Tab_anuncios_imoveis[estado]
    ),
    REMOVEFILTERS(Tab_anuncios_imoveis[id_url])
)
```

#### `P25_Grupo`

```dax
CALCULATE(
    PERCENTILE.INC(Tab_anuncios_imoveis[€/m2], 0.25),
    ALLEXCEPT(
        Tab_anuncios_imoveis,
        Tab_anuncios_imoveis[freguesia],
        Tab_anuncios_imoveis[tipo],
        Tab_anuncios_imoveis[tipologia],
        Tab_anuncios_imoveis[estado]
    ),
    REMOVEFILTERS(Tab_anuncios_imoveis[id_url])
)
```

#### `P75_Grupo`

```dax
CALCULATE(
    PERCENTILE.INC(Tab_anuncios_imoveis[€/m2], 0.75),
    ALLEXCEPT(
        Tab_anuncios_imoveis,
        Tab_anuncios_imoveis[freguesia],
        Tab_anuncios_imoveis[tipo],
        Tab_anuncios_imoveis[tipologia],
        Tab_anuncios_imoveis[estado]
    ),
    REMOVEFILTERS(Tab_anuncios_imoveis[id_url])
)
```

#### `N_Grupo`

```dax
VAR Grupo =
    FILTER(
        ALL(Tab_anuncios_imoveis),
        Tab_anuncios_imoveis[freguesia] = SELECTEDVALUE(Tab_anuncios_imoveis[freguesia]) &&
        Tab_anuncios_imoveis[tipo] = SELECTEDVALUE(Tab_anuncios_imoveis[tipo]) &&
        Tab_anuncios_imoveis[tipologia] = SELECTEDVALUE(Tab_anuncios_imoveis[tipologia]) &&
        Tab_anuncios_imoveis[estado] = SELECTEDVALUE(Tab_anuncios_imoveis[estado])
    )

RETURN
COUNTROWS(Grupo)
```

#### `Desvio%_Grupo`

```dax
DIVIDE(
    SELECTEDVALUE(Tab_anuncios_imoveis[€/m2]) - [Mediana_Grupo],
    [Mediana_Grupo]
)
```

#### `Classificacao_Preco_FIXO`

```dax
VAR Preco = SELECTEDVALUE(Tab_anuncios_imoveis[€/m2])
VAR P25 = [P25_Grupo]
VAR P75 = [P75_Grupo]

VAR Limite_Baixo = P25 * 0.90
VAR Limite_Alto  = P75 * 1.10

RETURN
SWITCH(
    TRUE(),
    Preco < Limite_Baixo, "Muito abaixo",
    Preco >= Limite_Baixo && Preco < P25, "Abaixo",
    Preco >= P25 && Preco <= P75, "Dentro",
    Preco > P75 && Preco <= Limite_Alto, "Acima",
    Preco > Limite_Alto, "Muito acima"
)
```

#### `Score_Oportunidade`

```dax
VAR Desvio = [Desvio%_Grupo]

-- inverter: negativo = bom
VAR ScoreBase = - Desvio

-- tamanho do grupo
VAR N = [N_Grupo]

VAR Fator_Grupo =
    DIVIDE(LOG(1 + N), LOG(51))   -- versão suave e robusta

-- classificação (AGORA É MEDIDA)
VAR Classe = [Classificacao_Preco_FIXO]

VAR BonusClasse =
    SWITCH(
        TRUE(),
        Classe = "Muito abaixo", 0.20,
        Classe = "Abaixo", 0.10,
        Classe = "Dentro", 0,
        Classe = "Acima", -0.10,
        Classe = "Muito acima", -0.20,
        0
    )

RETURN
(ScoreBase + BonusClasse) * Fator_Grupo
```

#### `Flag_TOP`

```dax
IF(
    [Score_Oportunidade] > 0.15,
    "🔥 Oportunidade",
    ""
)
```

### Cartões de texto

#### `Texto_Card` **[revisão out/2026]**

```dax
-- Antes: SUM(premio_energetico[premio]) somava todos os segmentos (14.772 €/m² sem filtros).
-- Agora: prémio B -> A (mediana A - mediana B), só com amostras >= 20 imóveis; média dos segmentos selecionados.
VAR p = CALCULATE([Prémio €/m² (n ≥ 20)], premio_energetico[classe_energetica] = "A")
RETURN
IF(
    ISBLANK(p),
    "Prémio B → A: amostra insuficiente (< 20 imóveis)",
    "Prémio B → A: " & FORMAT(p, "#,##0") & " €/m²"
)
```

#### `Texto_Card_2` **[revisão out/2026]**

```dax
-- Antes: MAX(indice_verde_geral[freguesia]) devolvia a última freguesia por ordem alfabética (Ramalde, 7.º lugar).
-- Agora: devolve a freguesia com melhor ranking_geral (1.º lugar no índice verde).
VAR Melhor =
    CALCULATE(
        MAX(indice_verde_geral[freguesia]),
        indice_verde_geral[ranking_geral] = 1
    )
RETURN
"Melhor freguesia para viver (índice verde): " & Melhor
```

### Medidas acrescentadas na revisão de outubro de 2026

#### `Mediana €/m²` **[revisão out/2026]**

```dax
MEDIAN(Tab_anuncios_imoveis[€/m2])
```

#### `Prémio €/m² (n ≥ 20)` **[revisão out/2026]**

```dax
-- Prémio de €/m² de uma classe face à classe imediatamente abaixo (ex.: B → A), 
-- só para segmentos (tipo × tipologia) com pelo menos 20 imóveis na classe.
-- Com vários segmentos selecionados, devolve a média dos segmentos válidos (nunca a soma).
CALCULATE(
    AVERAGE(premio_energetico[premio]),
    premio_energetico[n_amostra] >= 20,
    premio_energetico[premio] <> 0
)
```

#### `Pontos Carregadores EV` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_ev])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Ciclovias` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_ciclovias])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Desporto` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_desporto])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Escolas Básicas` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_eb])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Escolas Secundárias` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_es])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Espaços Verdes` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_verde])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Metro` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_metro])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```

#### `Pontos Saúde` **[revisão out/2026]**

```dax
8 - SUM(indice_verde_rankings[rank_csp])  -- 7 = 1.º lugar (melhor), 1 = 7.º lugar
```
