'''
Created on 2015/11/25

@author: FZY
'''


#the baseline of mase of two vlaue is 

'''
Created on 2015/11/4
@author: FZY
'''
import random
from sklearn.linear_model import Ridge,Lasso,LogisticRegression
from hyperopt import hp
import numpy as np
import pandas as pd
from hyperopt.pyll_utils import hyperopt_param
from sklearn.cross_validation import train_test_split
from sklearn.metrics import mean_squared_error,explained_variance_score,mean_absolute_error,auc
from sklearn.metrics import average_precision_score
from hyperopt import Trials,tpe,fmin
from hyperopt.base import STATUS_OK
from ml_metrics import accuracy_model,Ret_Plus_error,Ret_Plus_error_xgb
from sklearn.datasets import dump_svmlight_file
import os
import xgboost as xgb
from sklearn.svm import SVR,LinearSVR
import time
from CVModel import loadCVIndex
#fit the  param 
debug = False
xgb_random_seed = 2015

if debug:
    hyperopt_param = {}
    hyperopt_param['lasso_max_evals'] = 2
    hyperopt_param['ridge_max_evals'] = 2
    hyperopt_param['lr_max_evals'] = 2
    hyperopt_param["xgb_max_evals"] = 2
    hyperopt_param['svr_max_evals'] = 2
    hyperopt_param['lsvr_max_evals']=2
    xgb_min_num_round = 2
    xgb_max_num_round = 4
    xgb_nthread=32
    xgb_num_round_step = 1
else:
    hyperopt_param = {}
    hyperopt_param['ridge_max_evals'] = 400
    hyperopt_param['lasso_max_evals'] = 1
    hyperopt_param['lr_max_evals'] = 400
    hyperopt_param["xgb_max_evals"] = 400
    hyperopt_param['svr_max_evals'] = 400
    hyperopt_param['lsvr_max_evals'] = 100
    xgb_min_num_round = 200
    xgb_max_num_round = 300
    xgb_nthread= 8
    xgb_num_round_step = 10
    
Ridge_param= {
    'task':'skl_ridge',
    'alpha':  hp.loguniform("alpha", np.log(4), np.log(20)),
    'random_state':2015,
    'max_evals':hyperopt_param['ridge_max_evals']           
}

Lasso_param = {
    'task':'skl_lasso',
    'alpha': hp.loguniform("alpha", np.log(0.00001), np.log(20)),
    'random_state':2015,
    'max_evals':hyperopt_param['lasso_max_evals']       
}
"""
xgb_regression_param = {
    'task': 'regression',
    'booster': 'gblinear',
    'objective': 'reg:linear',
    'lambda' : hp.quniform('lambda', 0.001, 0.005, 0.001),
    'alpha' : hp.loguniform("alpha", np.log(1), np.log(5)),
    'num_round' : hp.quniform('num_round', xgb_min_num_round, xgb_max_num_round, xgb_num_round_step),
    'nthread': xgb_nthread,
    'silent' : 1,
    'seed': xgb_random_seed,
    "max_evals": hyperopt_param["xgb_max_evals"],                    
}
"""
xgb_regression_param = {
    'task': 'regression',
    'booster': 'gblinear',
    'objective': 'reg:linear',
    'lambda' : 0.1,
    'alpha' : 0.0,
    'num_round' : 120,
    'lambda_bias':0.2,
    'nthread': xgb_nthread,
    'silent' : 1,
    'seed': xgb_random_seed,
    "max_evals": hyperopt_param["xgb_max_evals"],                    
}
xgb_regression_param_by_tree = {
    'task': 'regression',
    'booster': 'gbtree',
    'objective': 'reg:linear',
    'eta' : hp.quniform('eta', 0.1, 1.0, 0.1),
    'eta':0.1,
    'gamma':hp.quniform('gamma',4,5,0.1),
    'gamma':4,
    'max_depth':12.0,
    'max_depth':hp.quniform('max_depth',6,15,1),
    'min_child_weight':hp.quniform('min_child_weight',1,5,1),
    'colsample_bytree':hp.quniform('colsample_bytree',0.5,1,0.1),
    'num_round' : hp.quniform('num_round', xgb_min_num_round, xgb_max_num_round, xgb_num_round_step),
    'nthread': xgb_nthread,
    'silent' : 1,
    'seed': xgb_random_seed,
    "max_evals": hyperopt_param["xgb_max_evals"],                    
}

xgb_tree_param = {
    'task': 'class',
    'booster': 'gbtree',
    'objective': 'multi:softmax',
    'eta' : hp.quniform('eta', 0.1, 1, 0.1),
    'gamma': hp.quniform('gamma',0.1,2,0.1),
    'num_round' : hp.quniform('num_round', xgb_min_num_round, xgb_max_num_round, xgb_num_round_step),
    'nthread': xgb_nthread,
    'silent' : 1,
    'seed': xgb_random_seed,
    "max_evals": hyperopt_param["xgb_max_evals"], 
    "num_class":  9,    
    'max_depth': hp.quniform('max_depth', 6, 12, 1),             
}

skl_lr_param = {
    'task' : 'skl_lr',
    'C' : hp.quniform('C',1,20,0.1),
    'seed':xgb_random_seed,
    'max_evals':hyperopt_param['lr_max_evals']
}

skl_LibSVM_param = {
    'task':'skl_LibSVM',
    'kernel':hp.choice('kernel',['rbf']),
    #'epsilon':hp.quniform('epsilon',0.2,0.6,0.1),
    'epsilon':hp.quniform('epsilon',0.01,0.02,0.01),

    'cache_size':1024.0, 
    'gamma':hp.quniform('gamma',0.05,0.1,0.01),  
    'max_evals':hyperopt_param['svr_max_evals'] 
}

skl_linearSVR_param= {
    'task' : 'skl_linearSVR',
    'epsilon':hp.quniform('epsilon',0.0001,0.0005,0.0001),
    'C' : hp.quniform('C',5,15,1),
    'loss':'squared_epsilon_insensitive',
    'seed':2015,
    'dual':False,
    'max_evals':hyperopt_param['lsvr_max_evals']
}



def dumpMessage(bestParams,loss,loss_std,f_name,start,end,feature):
     
    f = open("../../data/feature/weight/%s_%s_bestParamodel_log.txt"%(f_name,feature),"wb") 
    f.write('loss:%.6f \nStd:%.6f \n'%(loss,loss_std))
    for(key,value) in bestParams.items():
        f.write("%s:%s\n"%(key,str(value))) 
    f.write("start_time:%s\n"%(start))
    f.write("end_time:%s\n"%(end))
    f.close()  
def trainModel(param,data,features,feature):
    #we just judge our model
    #so we do not use bagging ,just one loop of CV
   
    train_feature = features
    pred_label = feature
    feature_valid = ['Ret_PlusOne','Ret_PlusTwo','Weight_Daily']
    #create CV
    err_cv = []
    std_cv = []
    for run in range(0,3):
        print "this is run:%d"%(run+1)
        train_index = loadCVIndex("../../data/cv/train.run%d.txt"%(run+1))
        test_index = loadCVIndex("../../data/cv/valid.run%d.txt"%(run+1))
        error_data = data.iloc[test_index]
        X_train = data.iloc[train_index][train_feature]
        X_test = data.iloc[test_index][train_feature]
        Y_train = data.iloc[train_index][pred_label]
        Y_test = data.iloc[test_index][pred_label]
        if param['task'] == 'skl_ridge': 
            ridge = Ridge(alpha=param['alpha'],normalize=True)
            ridge.fit(X_train,Y_train)
            pred_value = ridge.predict(X_test)
            pd.DataFrame(ridge.coef_,columns=train_feature).to_csv("ridge.csv")
            pred_value = pd.DataFrame(pred_value,columns=['1','2'])
            train_data = data.iloc[test_index]
            print train_data.shape
            error_train = Ret_Plus_error(pred_value,train_data[feature_valid])/(40000*0.7*62)
            print error_train
            variance = 0
            err_cv.append(error_train)
            std_cv.append(variance)
        elif param['task'] == 'skl_lasso':
            lasso = Lasso(alpha=param['alpha'],normalize=True,fit_intercept=True,tol=0.00000000001)
            lasso.fit(X_train,Y_train)
            pred_value = lasso.predict(X_test)
            pred_value = pd.DataFrame(pred_value,columns=['1','2'])
            train_data = data.iloc[test_index]
            error_train = Ret_Plus_error(pred_value,train_data[feature_valid])
            print error_train
            variance = 0
            err_cv.append(error_train)
            std_cv.append(variance)
        elif param['task'] == 'skl_lr':
            clf = LogisticRegression(C=param['C'])
            clf.fit(X_train,Y_train)
            pred_value = clf.predict(X_test)
            error_train = 1 - accuracy_model(pred_value, Y_test)
            variance = error_train
            err_cv.append(error_train)
            std_cv.append(variance)
            
        elif param['task'] == 'regression':
            train_data = xgb.DMatrix(X_train,label=np.array(Y_train))
            valid_data = xgb.DMatrix(X_test,label=np.array(Y_test))
            watchlist = [(train_data,'train'),(valid_data,'valid')]
            bst = xgb.train(param, train_data, int(param['num_round']),watchlist)
            valid_data = xgb.DMatrix(X_test)
            pred_value = bst.predict(valid_data)
            tmp_data = error_data[feature_valid]
            for feat in pred_label:
                print tmp_data.shape
                print pred_value.shape
                error_train = Ret_Plus_error_xgb(tmp_data,feat,list(pred_value))/(40000*0.3*62)
                variance = 0
                err_cv.append(error_train)
                std_cv.append(variance)
                print error_train
        elif param['task'] == 'class':
            train_data = xgb.DMatrix(X_train,label=Y_train)
            valid_data = xgb.DMatrix(X_test,label=Y_test)
            watchlist = [(train_data,'train'),(valid_data,'valid')]
            bst = xgb.train(param, train_data, int(param['num_round']),watchlist)
            valid_data = xgb.DMatrix(X_test)
            pred_value = bst.predict(valid_data)
            error_train = 1 - accuracy_model(pred_value, Y_test)
            variance = 0
            err_cv.append(error_train)
            std_cv.append(variance)
            print error_train
        elif param['task'] == 'skl_LibSVM':

            svr = SVR(epsilon=param['epsilon'],tol=param['tol'],cache_size=param['cache_size'],gamma=param['gamma'])
            svr.fit(X_train,Y_train['Ret_PlusOne'])
            pred_value1 = svr.predict(X_test)
            svr.fit(X_train,Y_train['Ret_PlusTwo'])
            pred_value2 = svr.predict(X_test)
            if param['kernel'] == 'linear':
                pd.DataFrame(svr.coef_,columns=train_feature).to_csv("svr.csv")
            pred_value = pd.DataFrame({'1':pred_value1,'2':pred_value2})
            train_data = data.iloc[test_index]
            error_train = Ret_Plus_error(pred_value,train_data[feature_valid])
            print error_train/(40000*0.3*62)
            variance = 0
            err_cv.append(error_train)
            std_cv.append(variance)
        elif param['task'] == 'skl_linearSVR':
            print param['epsilon']
            print param['C']
            svr = LinearSVR(C=param['C'],epsilon=param['epsilon'],dual=param['dual'],loss=param['loss'],random_state=param['seed'])
            svr.fit(X_train,Y_train['Ret_PlusOne'])
            pred_value1 = svr.predict(X_test)
            svr.fit(X_train,Y_train['Ret_PlusTwo'])
            pred_value2 = svr.predict(X_test)
            pred_value = pd.DataFrame({'1':pred_value1,'2':pred_value2})
            train_data = data.iloc[test_index]
            error_train = Ret_Plus_error(pred_value,train_data[feature_valid])
            print error_train/(40000*0.3*62)
            variance = 0
            err_cv.append(error_train)
            std_cv.append(variance)
    #print "error.train:%f error.test:%f"%(error_train,error)
    error = np.mean(err_cv)
    std_cv = np.mean(err_cv)
    print "error:%f"%(error)
    return {'loss':error,'attachments':{'std':variance},'status':STATUS_OK}


def TunningParamter(param,data,features,feature):
    ISOTIMEFORMAT='%Y-%m-%d %X'
    start = time.strftime(ISOTIMEFORMAT, time.localtime())
    trials = Trials()
    objective = lambda p : trainModel(p, data, features,feature)
    best_parameters = fmin(objective, param, algo =tpe.suggest,max_evals=param['max_evals'],trials= trials)
    #now we need to get best_param
    print best_parameters
    trials_loss = np.asanyarray(trials.losses(),dtype=float)
    best_loss = min(trials_loss)
    ind = np.where(trials_loss==best_loss)[0][0]
    best_loss_std = trials.trial_attachments(trials.trials[ind])['std']
    end = time.strftime(ISOTIMEFORMAT,time.localtime())
    dumpMessage(best_parameters, best_loss, best_loss_std,param['task'],start,end,feature)

if __name__ == "__main__":  

    train_price = pd.read_csv("../../data/train_ts_price.csv")
    train = pd.read_csv("../../data/train_clean_fill_all_2.csv")
    #add price message to train
    features = ["Ret_%d_price"%(i) for i in range(2,121)]
    train[features] = train_price[features]
    all_features= []
    #add the feature to predict
    features = [ "Feature_%d"%(i) for i in range(1,26)]
    all_features.extend(features) 
    
    features =["Ret_%d"%(i) for i in range(2,121)]
    all_features.extend(features) 
    features = ["Ret_%d_price"%(i) for i in range(2,121)]
    all_features.extend(features)
    
    all_features.append('Ret_total_price')
    all_features.append('Ret_mean')
    all_features.append('Ret_mean_price')
    all_features.append('Ret_max_price')
    all_features.append('Ret_max')
    all_features.append('Ret_min_price')
    all_features.append('Ret_min')
    all_features.append('Ret_var')
    all_features.append('Ret_var_price')
    all_features.append('Ret_120')
    
    lables = ['Ret_PlusOne','Ret_PlusTwo']
    TunningParamter(Ridge_param, train, all_features, lables)
    #lables = ['Ret_PlusOne','Ret_PlusTwo']
    #TunningParamter(skl_LibSVM_param, train, all_features, lables)
    #lables = ['Ret_PlusOne']
    #TunningParamter(xgb_regression_param, train, all_features,lables)
    #lables = ['Ret_PlusTwo']
    #TunningParamter(xgb_regression_param, train, all_features,lables)
    #lables = ['Ret_PlusOne']
    #TunningParamter(skl_linearSVR_param, train, all_features,lables)













