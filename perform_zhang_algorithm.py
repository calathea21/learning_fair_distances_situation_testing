import utils
from zhang_algorithm import give_discrimination_scores_zhang, make_model_admission, make_model_adult, give_decision_labels_zhang_unprotected_group

def admission_data_get_columns_info():
    interval_vars = ['A', 'Score', 'Extra Curricular']
    nominal_vars = []
    ordinal_vars = []

    columns_info = {'interval': interval_vars, 'nominal': nominal_vars, 'ordinal': ordinal_vars}
    return columns_info


def zhang_preprocessing_admission_train(train_data, sens_attribute, decision_attribute, column_info):
    #bin_dictionary = {'Score': 6, 'Extra Curricular': 6, 'Height': 3}
    bin_dictionary = {}
    train_data, bin_edges_dict = utils.bin_all_attributes_train(train_data, bin_dictionary)
    train_data['Admission'] = decision_attribute
    train_data['Gender'] = sens_attribute
    range_dict = utils.make_range_dict(train_data, column_info)
    model = make_model_admission(train_data)
    return train_data, bin_edges_dict, range_dict, model


def zhang_preprocessing_admission_test(test_data, bin_edges_dict, sens_attribute, decision_attribute):
    test_data = utils.bin_based_on_train_bins(test_data, bin_edges_dict)
    test_data['Admission'] = decision_attribute
    test_data['Gender'] = sens_attribute
    return test_data


def get_zhang_discrimination_scores_admission(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k):
    column_info = admission_data_get_columns_info()
    train_data, bin_edges_dict, range_dict, model = zhang_preprocessing_admission_train(train_data, train_sens_attribute, train_decision_attribute, column_info)
    test_data = zhang_preprocessing_admission_test(test_data, bin_edges_dict, test_sens_attribute, test_decision_attribute)
    discrimination_scores = give_discrimination_scores_zhang(model, 'Gender', 'Admission', train_data, test_data, k, column_info, range_dict, 1, 2)
    return discrimination_scores


def get_zhang_decision_scores_admission(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k):
    column_info = admission_data_get_columns_info()
    train_data, bin_edges_dict, range_dict, model = zhang_preprocessing_admission_train(train_data, train_sens_attribute, train_decision_attribute, column_info)
    test_data = zhang_preprocessing_admission_test(test_data, bin_edges_dict, test_sens_attribute, test_decision_attribute)
    discrimination_scores = give_decision_labels_zhang_unprotected_group(model, 'Gender', 'Admission', train_data, test_data, k, column_info, range_dict, 1, 2)
    return discrimination_scores


def adult_data_get_columns_info():
    interval_vars = ['age', 'capital.loss', 'hours.per.week', 'capital.gain']
    nominal_vars = ['race', 'marital.status', 'relationship', 'occupation', 'workclass']
    ordinal_vars = ['education.num']

    columns_info = {'interval': interval_vars, 'nominal': nominal_vars, 'ordinal': ordinal_vars}
    return columns_info


def cluster_categorical_attributes_adult(data):
    new_data = data.copy()
    new_data.loc[new_data['native.country'] != 'United-States', 'native.country'] = 'Other'
    return new_data

def zhang_preprocessing_adult_train(train_data, sens_attribute, decision_attribute, column_info):
    bin_dictionary = {'age': 5, 'hours.per.week':5, 'education.num': 15, 'capital.gain': 4, 'capital.loss': 4}
    train_data, bin_edges_dict = utils.bin_all_attributes_train(train_data, bin_dictionary)
    train_data = cluster_categorical_attributes_adult(train_data)
    train_data['Income'] = decision_attribute
    train_data['Gender'] = sens_attribute
    model = make_model_adult(train_data)
    range_dict = utils.make_range_dict(train_data, column_info)
    return train_data, bin_edges_dict, range_dict, model


def zhang_preprocessing_adult_test(test_data, bin_edges_dict, sens_attribute, decision_attribute):
    test_data = utils.bin_based_on_train_bins(test_data, bin_edges_dict)
    test_data['Income'] = decision_attribute
    test_data['Gender'] = sens_attribute
    return test_data


def get_zhang_discrimination_scores_adult(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k):
    column_info = adult_data_get_columns_info()
    train_data, bin_edges_dict, range_dict, model = zhang_preprocessing_adult_train(train_data, train_sens_attribute,
                                            train_decision_attribute, column_info)
    test_data = zhang_preprocessing_adult_test(test_data, bin_edges_dict, test_sens_attribute,
                                                    test_decision_attribute)
    discrimination_scores = give_discrimination_scores_zhang(model, 'Gender', 'Income', train_data, test_data, k,
                                                             column_info, range_dict, 1, 2)
    return discrimination_scores


def get_zhang_discrimination_scores(admission_or_adult, k, train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute):
    if admission_or_adult == "admission":
        return get_zhang_discrimination_scores_admission(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k)
    else:
        return get_zhang_discrimination_scores_adult(train_data, train_sens_attribute, train_decision_attribute, test_data,
                                              test_sens_attribute, test_decision_attribute, k)


def get_zhang_decision_scores_adult(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k):
    column_info = adult_data_get_columns_info()
    train_data, bin_edges_dict, range_dict, model = zhang_preprocessing_adult_train(train_data, train_sens_attribute, train_decision_attribute, column_info)
    test_data = zhang_preprocessing_adult_test(test_data, bin_edges_dict, test_sens_attribute, test_decision_attribute)
    discrimination_scores = give_decision_labels_zhang_unprotected_group(model, 'Gender', 'Income', train_data, test_data, k, column_info, range_dict, 1, 2)
    return discrimination_scores

def get_zhang_decision_scores_unprotected_group(admission_or_adult, k, train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute):
    if admission_or_adult == "admission":
        return get_zhang_decision_scores_admission(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k)
    else:
        return get_zhang_decision_scores_adult(train_data, train_sens_attribute, train_decision_attribute, test_data, test_sens_attribute, test_decision_attribute, k)