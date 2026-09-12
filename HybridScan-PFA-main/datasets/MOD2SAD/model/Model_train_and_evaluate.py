from pycaret.classification import *
import pandas as pd
import csv
import os
from pycaret.classification import load_model, predict_model
from sklearn.metrics import classification_report, confusion_matrix,accuracy_score, precision_score, recall_score, f1_score

import pygetwindow as gw
import pyautogui
import time

def train(data_path,model_name,i):
    data = pd.read_csv(data_path)

    # 检查数据
    # print(data.head())

    # 设置实验（目标列名为'target'，请替换为你的目标列名）
    exp = setup(
        data=data,
        target='label',  # 你的二分类目标变量名
        train_size=0.7,   # 训练集比例
        normalize=True,   # 自动标准化数据（对神经网络很重要）
        session_id=123,   # 随机种子
        use_gpu=True,      # 如果使用GPU加速
        html=False,
        verbose=False,
        log_plots=False,
        profile=False,
        fold = 10,
    )

    X_test = get_config('X_test')
    y_test = get_config('y_test')
    test_data = X_test.copy()
    test_data['label'] = y_test

    model = create_model(
        model_name,
        # device='gpu',
        # tree_learner = 'data',
        # max_bin = 63
        )
    # optimize_metric = 'Accuracy' if i == 'A-3' else 'F1' # 不平衡数据集的模型优化需要使用F1指标

    tuned_model = tune_model(
        model,
        optimize='Accuracy',
        n_iter=250, # 超参数搜索迭代次数（建议50-100）
        choose_better=True, # 始终选择更好的模型
        early_stopping=True,
        # search_library='optuna',  # 比默认更快
        # search_algorithm='tpe',
    )

    print("模型训练结束，开始测试数据")
    predictions = predict_model(tuned_model, data=data)
    y_true = data['label']
    y_pred = predictions['prediction_label']

    acc = accuracy_score(y_true, y_pred)
    pre = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    filename = f'model_test_{i}_result.csv'
    result_path = os.path.join('F:\\科研文献撰写\\基于LLM解混淆的Office检测框架\\Project\\项目本体\\new_采用deepseek-coder,采用特征级联,采用次数统计\\model',filename)
    with open(result_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([model_name,acc,pre,rec,f1,tp,tn,fp,fn])

    # 保存最终模型
    model_path = save_model(tuned_model, f'F:\\科研文献撰写\\基于LLM解混淆的Office检测框架\\Project\\项目本体\\new_采用deepseek-coder,采用特征级联,采用次数统计\\model\\best_{model_name}_model_{i}')

    # 最优超参数保存
    filename = f'{i}_best_{model_name}_params.txt'
    result_path = os.path.join('F:\\科研文献撰写\\基于LLM解混淆的Office检测框架\\Project\\项目本体\\new_采用deepseek-coder,采用特征级联,采用次数统计\\model',filename)
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(str(tuned_model.get_params()))


    # # 在测试集上评估模型
    # print("开始评估模型")
    # evaluate_model(tuned_mlp)
    # check_and_close_popup()

    # 生成详细报告（包括混淆矩阵、AUC曲线等）
    # plot_model(tuned_mlp, plot='auc')        # AUC曲线
    # plot_model(tuned_mlp, plot='confusion_matrix')  # 混淆矩阵

    # 特征重要性分析
    # interpret_model(tuned_mlp, plot='summary')

def model_main(path_list):
    model_list = ['rf','et','xgboost','lightgbm','svm','lr','mlp']
    # model_list = ['et']
    for i in path_list:
        filename = f'model_test_{i}_result.csv'
        result_path = os.path.join('F:\\科研文献撰写\\基于LLM解混淆的Office检测框架\\Project\\项目本体\\new_采用deepseek-coder,采用特征级联,采用次数统计\\model',filename)
        with open(result_path,'a',encoding='utf-8') as f:
                writer = csv.writer(f)
                title = ['model_name','ACC','PRE','REC','F1','TP','TN','FP','FN']
                writer.writerow(title)
        for m_name in model_list:
            data_path = f"F:\\科研文献撰写\\基于LLM解混淆的Office检测框架\\Project\\项目本体\\new_采用deepseek-coder,采用特征级联,采用次数统计\\expriment_data\\train_data_{i}.csv"
            model_name = m_name
            print(f"开始训练模型：{m_name}")
            model_path = train(data_path,model_name,i) # 训练模型
            # model_path = 'F:\\科研文献撰写\\基于LLM解混淆的Office检测框架\\Project\\项目本体\\new_采用deepseek-coder,采用特征级联,采用次数统计\\model\\best_rf_model_A-3.pkl'

            # print(f"训练结束，开始测试模型：{m_name}")
            # predict(model_path,data_path,i)
    
# path_list = ['A-3', 'A-2', 'A-1']
path_list = ['S-A-DSC']
# model_main(path_list)
