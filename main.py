import streamlit as st
import pandas as pd
import statsmodels.api as sm
from datetime import datetime, timedelta


def date_to_datetime(current_date):
    return datetime.combine(current_date, datetime.min.time())


def display_title(text, level=1):
    st.markdown(
        f"""
        <h{level} style='text-align: center'>
            {text}
        </h{level}>
        """,
        unsafe_allow_html=True,
    )


def display_reflections():
    with st.expander("Размышления по поводу выбираемого времени"):
        st.markdown("**1 мая**. Много людей собрались вместе → много заболевших")
        st.markdown(
            "Представим, что люди, которые наиболее **уязвимы для смерти**, \
            погибают **достаточно быстро** (условно — 1 неделя), \
            но выздоровление проходит медленно (к примеру, через 2 недели)"
        )
        st.markdown("**7 мая**. Пусть к этому времени люди решили сидеть дома → **мало заболевших**.")
        st.markdown(
            "Что в итоге? На 7 мая много погибших, но выздоровевших и заболевших — мало. \
        **Говорит ли это о высокой летальности? Нет**, так как учитывались разные люди, а большое количество тех, \
        которые заболевали 1 мая начниуть выздоравливать гораздо позже, и сейчас их не получится учесть. \
        Поэтому брать статистику за день мне кажется не совсем целесообразно — **лучше брать за более долгий период**."
        )


POPULATION = {
    "Санкт-Петербург": 5384342,
    "Москва": 12655050,
}

OPTIONS_TO_COLUMN_NAMES = {
    "Смерти": "Смертей за день",
    "Заражения": "Заражений за день",
    "Выздоровления": "Выздоровлений за день",
}


def get_total_number_from_options(options, region_data):
    try:
        return sum(
            list(
                map(
                    lambda x: POPULATION[region_data["Регион"].iloc[0]]
                    if x == "Население"
                    else region_data[OPTIONS_TO_COLUMN_NAMES[x]].sum(),
                    options,
                )
            )
        )
    except KeyError:
        st.error(f"Для региона \"{region_data['Регион'].iloc[0]}\" нет данных для населения")
        return 0


def display_result(significance_level, p_value):
    if p_value >= significance_level:
        st.markdown(
            fr"${p_value} \geq \alpha={significance_level} \Rightarrow$ гипотеза о равенстве долей не отвергается"
        )
    else:
        st.markdown(fr"${p_value} < \alpha={significance_level} \Rightarrow$ гипотеза о равенстве долей отвергается")


def main():
    display_title("A/B Тестирование<h1 style='text-align: center'>Тест для пропорций</h1>")
    display_title("😷 Covid в России", 2)
    display_title("Данные на 29 октября 2021", 5)

    display_reflections()

    covid_russia = pd.read_csv("russia_covid.csv")
    covid_russia["Дата"] = pd.to_datetime(covid_russia["Дата"], format="%d.%m.%Y")

    regions = tuple(covid_russia["Регион"].unique())
    city_col1, city_col2 = st.columns(2)

    # Тюменская обл., Свердловская обл.
    first_region = city_col1.selectbox("Выберите два региона", regions, index=regions.index("Москва"))
    second_region = city_col2.selectbox("", regions, index=regions.index("Санкт-Петербург"))
    min_date = date_to_datetime(covid_russia["Дата"].min().date())
    max_date = date_to_datetime(covid_russia["Дата"].max().date())
    initial_start_date = max_date - timedelta(days=14)

    date_col1, date_col2 = st.columns(2)
    start_date = date_to_datetime(
        date_col1.date_input(
            "Введите начальную дату периода", value=initial_start_date, min_value=min_date, max_value=max_date
        )
    )
    timedelta_as_days = date_col2.number_input("Введите число дней в периоде", value=14, min_value=1, format="%i") - 1
    final_date = start_date + timedelta(days=timedelta_as_days)
    if final_date > max_date:
        st.error("Для части этого периода нет данных. Пожалуйста, выберите период поменьше.")
    else:
        success_options = st.multiselect(
            'Выберите опиции, которые будут входить в число "успехов" (будет суммироваться за пероид)',
            list(OPTIONS_TO_COLUMN_NAMES),
            default=["Смерти"],
        )
        total_number_of_tests_options = st.multiselect(
            "Выберите опиции, которые будут входить в общее число испытаний (будет суммироваться за пероид)",
            list(OPTIONS_TO_COLUMN_NAMES) + ["Население"],
            default=["Заражения"],
        )

        significance_levels = st.multiselect(
            "Выберите уровни значимости", [0.001, 0.01, 0.05], default=[0.001, 0.01, 0.05]
        )

        first_region_data = covid_russia[
            (covid_russia["Регион"] == first_region) & (covid_russia["Дата"].between(start_date, final_date))
        ]
        second_region_data = covid_russia[
            (covid_russia["Регион"] == second_region) & (covid_russia["Дата"].between(start_date, final_date))
        ]

        first_success_number = get_total_number_from_options(success_options, first_region_data)
        second_success_number = get_total_number_from_options(success_options, second_region_data)
        first_total_number = get_total_number_from_options(total_number_of_tests_options, first_region_data)
        second_total_number = get_total_number_from_options(total_number_of_tests_options, second_region_data)

        display_title("Результат", 2)
        z_label, p_value = sm.stats.proportions_ztest(
            [first_success_number, second_success_number], [first_total_number, second_total_number]
        )

        total_numbers = pd.DataFrame.from_dict(
            {
                first_region: [
                    first_success_number,
                    first_total_number,
                    first_success_number / first_total_number * 100,
                ],
                second_region: [
                    second_success_number,
                    second_total_number,
                    second_success_number / second_total_number * 100,
                ],
            },
            orient="index",
            columns=['Количество "успехов"', "Количество испытаний", 'Процент "успехов"'],
        )
        st.dataframe(total_numbers)

        st.markdown(f"**Z-метка**: $\; {z_label}$")
        st.markdown(f"**P-value**: $\; {p_value}$")

        for significance_level in significance_levels:
            display_result(float(significance_level), p_value)


if __name__ == "__main__":
    main()
