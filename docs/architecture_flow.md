# Architektura projektu i przepływ danych

Ten dokument przedstawia główne komponenty projektu, przepływ danych oraz zależności pomiędzy częścią integracyjną i częścią główną aplikacji.

Projekt składa się z dwóch części:

1. **Część integracyjna** — odpowiada za ręczne pozyskanie danych publicznych, lokalne przygotowanie danych, opcjonalne skanowanie folderu datasetu oraz wybór plików wejściowych.
2. **Część główna aplikacji** — obejmuje aplikację Streamlit, Data Cleaner & QC, Analysis Engine oraz generator raportu końcowego PDF.

Projekt pracuje na gotowych macierzach ekspresji genów i metadanych próbek. Nie pobiera automatycznie danych z GEO ani TCGA API i nie analizuje surowych danych FASTQ/BAM.

## Diagram przepływu danych

```mermaid
flowchart LR

    A[Publiczne dane / lokalny folder datasetu] --> B[Opcjonalne skrypty przygotowujące dane]
    B --> C[Macierz ekspresji + metadane]

    subgraph INTEGRACJA["Część integracyjna"]
        C --> D[Dataset Intake - opcjonalny]
        D --> D1[dataset_intake_report.csv]
        D --> D2[selected_input_files.csv]
    end

    subgraph APLIKACJA["Część główna - aplikacja Streamlit"]
        E[Streamlit UI] --> F[Manual upload]
        E --> D

        F --> G[Wybrane pliki wejściowe]
        D --> G

        G --> H[Data Cleaner & QC]

        H --> H1[clean_expression_matrix.csv]
        H --> H2[clean_metadata.csv]
        H --> H3[audit_log.csv]
        H --> H4[harmonization_report.csv]
        H --> H5[data_quality_report.csv]
        H --> H6[data_readiness_report.csv]
        H --> H7[QC plots]

        H1 --> I[Analysis Engine]
        H2 --> I

        I --> I1[Dataset Overview]
        I --> I2[Class Distribution]
        I --> I3[Most Variable Genes]
        I --> I4[PCA]
        I --> I5[Heatmap]
        I --> I6[Sample Clustering]
        I --> I7[analysis_summary.csv / analysis_summary.md]

        H3 --> J[Final PDF Report Generator]
        H4 --> J
        H5 --> J
        H6 --> J
        H7 --> J
        I1 --> J
        I2 --> J
        I3 --> J
        I4 --> J
        I5 --> J
        I6 --> J
        I7 --> J

        J --> K[final_report.pdf]
    end
```

## Opis komponentów

### 1. Publiczne dane / lokalny folder datasetu

Dane wejściowe pochodzą z publicznych źródeł, ale są pobierane i przygotowywane lokalnie. Projekt nie wykonuje automatycznego pobierania danych z zewnętrznych API.

### 2. Opcjonalne skrypty przygotowujące dane

Skrypty w katalogu `scripts/` służą do przygotowania przykładowych datasetów demonstracyjnych lub walidacyjnych. Nie są wymagane do standardowego działania aplikacji Streamlit.

### 3. Dataset Intake

Opcjonalny moduł skanujący lokalny folder datasetu. Identyfikuje kandydatów na macierz ekspresji i metadane, oblicza wynik punktowy oraz poziom pewności. Automatyczny wybór plików następuje tylko wtedy, gdy decyzja jest jednoznaczna.

### 4. Manual upload

Alternatywna ścieżka wejścia danych. Użytkownik może ręcznie wgrać macierz ekspresji i plik metadanych przez interfejs Streamlit.

### 5. Data Cleaner & QC

Moduł odpowiedzialny za harmonizację danych, czyszczenie wartości nienumerycznych, obsługę missing values, wykrywanie duplikatów, kontrolę metadanych oraz generowanie raportów jakości.

### 6. Analysis Engine

Moduł wykonujący eksploracyjną analizę danych po czyszczeniu. Obejmuje Dataset Overview, Class Distribution, Most Variable Genes, PCA, Heatmap oraz Sample Clustering.

### 7. Final PDF Report Generator

Moduł generujący raport końcowy zawierający podsumowanie danych, QC, cleaning, harmonizacji, analizy eksploracyjnej, wizualizacji oraz ograniczeń metodologicznych.

## Zasada działania

Projekt działa zgodnie z zasadą:

**Rule-Based Cleaning with Transparent Reporting**

Każda automatyczna decyzja musi być oparta na jawnej regule, zapisana w audit logu lub raporcie i możliwa do odtworzenia. Jeśli decyzja nie jest jednoznaczna, system oznacza problem jako `WARNING`, `FAIL` albo `REQUIRES REVIEW`.
