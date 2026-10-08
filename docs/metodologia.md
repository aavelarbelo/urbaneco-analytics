# Metodologia e limitações — dashboard UrbanEco

Este documento reproduz a página **Metodologia** do relatório Power BI (versão de 7 de outubro de 2026).

## Dados

- **Fonte:** anúncios de venda do portal SuperCasa, concelho do Porto (7 freguesias, segundo as uniões de 2013).
- **Recolha:** scraper em Python/Selenium.
- **Período:** anúncios registados na base PostgreSQL do grupo entre 21 e 26/06/2026. Última atualização do relatório: 26/06/2026.
- **Amostra:** 2.874 anúncios com ID único.
  - 695 anúncios formam 263 grupos com preço, área, freguesia, tipologia e estado iguais. Destes, 469 são obra nova, onde é normal haver frações iguais no mesmo prédio.
  - Os grupos foram mantidos, porque não alteram a mediana (5.087 €/m²).
- **Classe energética:** "A+" é contada como "A" e "B-" como "B" (transformação feita no Power Query). NT significa sem certificado energético (148 anúncios).

## Métricas

- **€/m²** = preço pedido ÷ área útil. Usa-se a mediana (5.087 €/m²) e não a média (5.615 €/m²), porque os preços são assimétricos.
- **% A/B** é calculada sobre os imóveis certificados, ou seja, exclui os 148 NT. O valor é 69,26%. Sobre o total seria 65,7%.
- **EVI (0–100)** = (Price Score × 0,4 + Energy Score × 0,3 + Location Score × 0,3) × 20.
  - É calculado para 2.678 anúncios.
  - Fica em branco para os NT, que não têm Energy Score, e para segmentos com menos de 4 anúncios, que não têm Price Score.
- **Score de oportunidade:**
  - mede o desvio do €/m² do anúncio face à mediana do seu grupo (freguesia × tipo × tipologia × estado);
  - inclui um bónus segundo a posição face aos quartis P25/P75 do grupo;
  - é ponderado pelo tamanho do grupo.
- **Prémio verde:**
  - é a diferença entre as medianas de €/m² de classes energéticas consecutivas (por exemplo B → A), calculada por tipo × tipologia;
  - só entram segmentos com pelo menos 20 imóveis;
  - quando há vários segmentos, mostra-se a média e nunca a soma.
- **Serviços por freguesia:** pontuação = 8 − posição no ranking. O 1.º lugar vale 7 pontos.

## Filtros aplicados em visuais

- **Visão Geral, gráfico de classes energéticas:** exclui os NT. Por isso a percentagem é sobre os imóveis certificados.
- **Página EVI:**
  - o card da mediana conta só os imóveis com EVI ≥ 50;
  - o gráfico "EVI vs €/m²" mostra só os anúncios com €/m² abaixo de 12.000.
- **Oportunidades de Negócio:** mostra só os anúncios com €/m² ≥ 500 e marcados como oportunidade.
- **Prémio Verde:** usa só segmentos (tipo × tipologia) com pelo menos 20 imóveis na classe.

## Limitações

- São preços pedidos nos anúncios, não preços de transação.
- Houve uma única recolha (junho de 2026). O relatório não é atualizável sem acesso à base de dados do grupo.
- 65,7% da amostra total é A/B (69,3% dos certificados), acima do que é típico no parque habitacional português.
  - A explicação provável é o peso da obra nova: 91% da obra nova certificada é A/B, contra 50% dos usados.
- Os resultados mostram associação, não causalidade.
- **Qualidade de dados:**
  - 11 anúncios T0 têm mais de 100 m²;
  - 1 anúncio abaixo de 500 €/m² entra nos KPIs;
  - há possíveis anúncios repetidos com IDs diferentes (ver "Dados").
- As tabelas auxiliares (medianas por segmento e prémio verde) vêm da base do grupo.
  - Diferem em 1 anúncio em 6 segmentos.
  - O prémio não junta A+ com A.
