import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd


class ExcelIO:
    def __init__(self, df=None, path=None):
        self.df = df
        self.path = path

    def import_csv(self):
        self.path = os.path.dirname(os.path.abspath(__file__)) + "/"
        self.df = pd.read_csv(self.path + "2019年香港自殺資料統計 - 每日個案記錄.csv", header=4)


excel = ExcelIO()
excel.import_csv()


class Reformer:
    def __init__(self, df=None):
        self.df = df

    def drop_column(self):
        self.df.drop(['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'Unnamed: 4', 'Unnamed: 6', 'Unnamed: 10',
                      'Unnamed: 11', 'Unnamed: 13', 'Unnamed: 14', 'Unnamed: 16', 'Unnamed: 17', 'Unnamed: 20',
                      '傳送', '類別', 'Unnamed: 37', '報導來源'], axis=1, inplace=True)

    def drop_possible_column(self):
        self.df.drop(['Unnamed: 19', '緯度', '經度', 'Unnamed: 29',
                      '原因2', '原因3', '地區', '街道 / 屋邨 / 建築',
                      '門牌 / 樓宇 / 地點'], axis=1, inplace=True)

    # ===== ===== ===== #
    def rename_header(self):
        self.df.rename(columns={'Unnamed: 5': 'Weekday', 'Unnamed: 25': 'Housing_or_not', 'Unnamed: 26': 'Housing_Type',
                                'Unnamed: 35': 'Suicide_Method'}, inplace=True)

    def fill_for_na(self):
        self.df[['星期六日及公眾假期', '星期日及勞工假期']] = \
            self.df[['星期六日及公眾假期', '星期日及勞工假期']].fillna(value='平日')

    def fill_with_avg_age(self):
        self.df['年齡'] = self.df['年齡'].apply(lambda x: int(x.replace("不詳", "44")))
        self.df['student'] = self.df['年齡'].apply(lambda x: 1 if x <= 22 else 0)

    # =============== #
    def update_date(self):
        self.df['MM'] = self.df['個案發現日期'].apply(lambda x: x[x.find('年')+1: x.find('月')])
        self.df['MM_Pos'] = self.df['個案發現日期'].apply(
            lambda x: 'Start' if int(x[x.find('月') + 1: x.find('日')]) <= 10
            else ('Middle' if int(x[x.find('月') + 1: x.find('日')]) <= 20 else 'End'))
        self.df.drop(['個案發現日期'], axis=1, inplace=True)
        self.df['protest'] = self.df['MM'].apply(lambda x: 1 if int(x) >= 6 else 0)

    def change_weekday_as_int(self):
        self.df['Weekday_int'] = self.df['Weekday'].\
            map({'星期日': 7, '星期一': 1, '星期二': 2, '星期三': 3, '星期四': 4, '星期五': 5, '星期六': 6})
        self.df.drop(['Weekday'], axis=1, inplace=True)

    def change_case_of_day_as_int(self):
        self.df['Case_of_Day'] = self.df['當天'].apply(lambda x: int(''.join(filter(str.isdigit, x))))
        self.df.drop(['當天'], axis=1, inplace=True)

    def update_time(self):
        self.df['Hour'] = self.df['時間'].apply(
            lambda x: int(x[2: x.find('時')].replace('零', '0')) + 12
            if x[:2] in ['下午', '傍晚', '晚上', '深夜', '黃昏'] else int(x[2: x.find('時')].replace('零', '0')))
        self.df.drop(['時間'], axis=1, inplace=True)
        self.df['Period'] = self.df['Hour'].apply(lambda x: x % 6)  # midnight, morning, afternoon, night
        self.df['警察更別'] = self.df['Hour'].apply(
            lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 24 else 'C'))
        self.df['警察當更時數'] = self.df['Hour'].apply(lambda x: x % 8 + 1)

    # ===== ===== ===== #
    def group_reason(self):
        self.df['原因1'] = self.df['原因1'].apply(
            lambda x: x.replace('藥品', '酒精').replace('酒精', '酒精藥品'))

    def group_suicide_method(self):
        self.df['Suicide_Method'] = self.df['Suicide_Method'].apply(
            lambda x: x.replace('不詳', '跳落').replace('槍械', '出血')
        )

    def indicate_possible_protestor(self):
        self.df['protestor_indicator'] = (self.df['student'] + self.df['protest'] == 2)

    def main(self):
        self.drop_column()
        self.drop_possible_column()
        self.rename_header()
        self.fill_for_na()
        self.fill_with_avg_age()

        self.update_date()
        self.change_weekday_as_int()
        self.change_case_of_day_as_int()
        self.update_time()
        self.group_reason()
        self.group_suicide_method()
        self.indicate_possible_protestor()


reformed = Reformer(excel.df.copy())
reformed.main()


class ChartAndPivot:
    def __init__(self, df, cross_tab=None, cross_tab2=None, pivot=None, bar=None):
        self.df = df
        self.cross_tab = cross_tab
        self.cross_tab2 = cross_tab2
        self.pivot = pivot
        self.bar = bar

    # compare the relationship between protest and suicide method
    # find that free fall during Protest is much more.
    def build_cross_tab_4_protester(self):
        self.cross_tab = pd.crosstab(
            index=reformed.df['protestor_indicator'], columns=self.df['Suicide_Method'],
            values=self.df['死亡'], aggfunc='count', normalize='index')

    # consider the suicide rate:
    # 1) new territory is higher,
    # x) 非住, female is little higher.
    # x) no suicide reason is less, but the suicide reason =  love, life is higher
    # 4) period = middle is higher
    # 5) saturday is higher
    # 6) evening is higher
    # *) 中更處理自殺案比例由28%(正常) 升至42% (運動)
    # 8) 運動期間自殺案，警察較多在頭1小時或臨放工時處理
    # below is just one of the example about new territory
    def build_cross_tab_4_protester_2(self):
        self.cross_tab2 = pd.crosstab(index=reformed.df['protestor_indicator'],
                                      columns=reformed.df['警察更別'],
                                      values=reformed.df['死亡'],
                                      aggfunc='count', normalize='index')

    # 00:00 to 04:00 has higher suicide rate
    # Tuesday and Wednesday night also has higher rate
    def build_pivot_against_weekday_n_period(self):
        self.pivot = pd.pivot_table(
            self.df, values=['死亡'], columns=['Weekday_int'],
            index=['Period', ], aggfunc='count')

    @staticmethod
    def create_bar_chart():
        labels = ['Traffic', 'Bleeding', 'Toxic', 'asphyxia', 'Self-immolation', 'Falling']
        false_value = np.round(charted.cross_tab.values[0], 2)
        true_value = np.round(charted.cross_tab.values[1], 2)
        x = np.arange(len(labels))  # the label locations
        width = 0.35  # the width of the bars
        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width / 2, false_value, width, label='False')
        rects2 = ax.bar(x + width / 2, true_value, width, label='True')
        ax.set_ylabel('Percentage')
        ax.set_title('Percentage By Indicators and Reason')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        def auto_label(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate('{}'.format(height),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
        auto_label(rects1)
        auto_label(rects2)
        fig.tight_layout()
        plt.show()

    @staticmethod
    def create_pie_chart():
        fig, axs = plt.subplots(1, 2)
        labels = 'Traffic', 'Bleeding', 'Toxic', 'asphyxia', 'Self-immolation', 'Falling'
        false_value = np.round(charted.cross_tab.values[0], 2)
        true_value = np.round(charted.cross_tab.values[1], 2)
        axs[0].pie(false_value, labels=labels, autopct='%1.1f%%', shadow=True)
        axs[1].pie(true_value, labels=labels, autopct='%1.1f%%', shadow=True)
        plt.show()

    def main(self):
        self.build_cross_tab_4_protester()
        self.build_cross_tab_4_protester_2()
        self.build_pivot_against_weekday_n_period()
        # self.create_pie_chart()


charted = ChartAndPivot(reformed.df.copy())
charted.main()

# ===== ===== ===== #
# test = reformed.df.sort_values(by=['十八區'], ascending=[True, True])
