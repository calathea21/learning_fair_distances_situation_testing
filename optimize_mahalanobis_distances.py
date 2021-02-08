import numpy as np
from scipy.optimize import minimize
import math
from optimize_distances_utils import calc_distances_within_and_between_classes, get_instances_with_same_and_different_class_label, \
    give_difference_vector_between_instances
from optimize_distances_utils import SDProject, metric_to_linear
from sklearn.utils.validation import check_X_y, check_array
from numpy.linalg import norm, cholesky


#This function gives the mahalanobis distance between two instances x and y
def mahalanobis_distance(x, y, weight_matrix, indices_info):
    # weight_matrix = np.reshape(weight_array, (len(x), len(x)))
    abs_difference = give_difference_vector_between_instances(x, y, indices_info)
    transposed_difference = np.transpose(abs_difference)
    dot_product1 = np.matmul(transposed_difference, weight_matrix)
    distance = np.matmul(dot_product1, abs_difference)
    if (distance - 0.0 < 1e-9):
        return 0.0
    return math.sqrt(distance)
    # return math.sqrt(np.matmul(dot_product1, abs_difference))


def mahalanobis_distance_given_abs_diff(abs_diff, weight_matrix):
    # weight_matrix = np.reshape(weightarray, (len(abs_diff), len(abs_diff)))
    transposed_difference = np.transpose(abs_diff)
    dot_product1 = np.matmul(transposed_difference, weight_matrix)
    distance = np.matmul(dot_product1, abs_diff)
    if (distance - 0.0 < 1e-9):
        return 0.0
    return math.sqrt(distance)
    # return math.sqrt(np.matmul(dot_product1, abs_diff))


def objective_mahalanobis(weights, protected_data, unprotected_data, protected_labels, unprotected_labels, indices_info, lambda_l1_norm):
    prot_dist_diff, prot_dist_same = calc_distances_within_and_between_classes(protected_labels, protected_data,
                                                                               weights, indices_info,
                                                                               mahalanobis_distance)
    unprot_dist_diff, unprot_dist_same = calc_distances_within_and_between_classes(unprotected_labels, unprotected_data,
                                                                                   weights, indices_info,
                                                                                   mahalanobis_distance)
    dist_same_classes = prot_dist_same + unprot_dist_same
    dist_diff_classes = prot_dist_diff + unprot_dist_diff

    mean_dist_same = sum(dist_same_classes) / len(dist_same_classes)
    mean_dist_diff = sum(dist_diff_classes) / len(dist_diff_classes)

    l1_norm = lambda_l1_norm * sum(sum(weights))

    print(weights)
    print(-(mean_dist_same - mean_dist_diff+l1_norm))
    return -(mean_dist_same - mean_dist_diff+l1_norm)


def make_mahalanobis_derivative_per_label_group(number_of_attributes, label_group, weightarray):
    derivative_vector = []
    for i in range(number_of_attributes):
        for j in range(number_of_attributes):
            sum_of_elements = 0
            for element in range(len(label_group)):
                mahalanobis_distance = mahalanobis_distance_given_abs_diff(label_group[element], weightarray)
                if mahalanobis_distance != 0:
                    sum_of_elements += ((1/(2*mahalanobis_distance)) * label_group[element][i] * label_group[element][j])
            derivative_vector.append(sum_of_elements)
    return derivative_vector


def mahalanobis_derivative(weights, protected_data, unprotected_data, protected_labels, unprotected_labels, indices_info, lambda_l1_norm):
    prot_same, prot_diff = get_instances_with_same_and_different_class_label(protected_labels, protected_data, indices_info)
    unprot_same, unprot_diff = get_instances_with_same_and_different_class_label(unprotected_labels, unprotected_data, indices_info)

    number_of_same = len(prot_same) + len(unprot_same)
    number_of_different = len(prot_diff) + len(unprot_diff)

    derivative_prot_same = np.array(make_mahalanobis_derivative_per_label_group(len(protected_data[0]), prot_same, weights))
    derivative_prot_diff = np.array(make_mahalanobis_derivative_per_label_group(len(protected_data[0]), prot_diff, weights))
    derivative_unprot_same = np.array(make_mahalanobis_derivative_per_label_group(len(protected_data[0]), unprot_same, weights))
    derivative_unprot_diff = np.array(make_mahalanobis_derivative_per_label_group(len(protected_data[0]), unprot_diff, weights))

    derivative_same = 1 / number_of_same * (derivative_prot_same + derivative_unprot_same)
    derivative_diff = 1 / number_of_different * (derivative_prot_diff + derivative_unprot_diff)

    derivative = -(derivative_same - derivative_diff + lambda_l1_norm)
    derivative = np.reshape(derivative, (3,3))
    return derivative


def optimize_mahalanobis(data, class_label, protected_attribute, indices_info, protected_label, unprotected_label):
    protected_labels = class_label[np.where(protected_attribute == protected_label)]
    unprotected_labels = class_label[np.where(protected_attribute == unprotected_label)]

    protected_data = data[np.where(protected_attribute == protected_label)]
    unprotected_data = data[np.where(protected_attribute == unprotected_label)]

    initial_weights = [0.1] * (len(data[0])*len(data[0]))

    b = (0.0, float('inf'))
    bds = [b] * (len(data[0])*len(data[0]))

    lambda_l1_norm = 0.1

    sol = minimize(objective_mahalanobis, initial_weights, (protected_data, unprotected_data, protected_labels, unprotected_labels, indices_info, lambda_l1_norm),
                   jac=mahalanobis_derivative, bounds=bds)

    return sol['x']



def optimize_mahalanobis(data, class_label, protected_attribute, indices_info, protected_label, unprotected_label, lambda_l1_norm):
    number_of_features = data.shape[1]

    # initialize weight matrix: ensure that it's quadratic, symmetric and psd.
    weight_matrix = np.zeros((number_of_features, number_of_features), float)
    np.fill_diagonal(weight_matrix, 0.00001)

    protected_labels = class_label[np.where(protected_attribute == protected_label)]
    unprotected_labels = class_label[np.where(protected_attribute == unprotected_label)]

    protected_data = data[np.where(protected_attribute == protected_label)]
    unprotected_data = data[np.where(protected_attribute == unprotected_label)]

    #hyperparameters that can be adjusted
    num_its = 0
    max_iter = 75
    err = 1e-3
    eta = 0.1

    # Metadata
    print(weight_matrix)
    initial_objective = objective_mahalanobis(weight_matrix, protected_data, unprotected_data, protected_labels, unprotected_labels, indices_info, lambda_l1_norm)
    current_objective = initial_objective

    last_weight_matrix = weight_matrix
    done = False

    while not done:
        ################## Projection ##################
        weight_matrix = (weight_matrix + weight_matrix.T) / 2.0
        weight_matrix = SDProject(weight_matrix).astype(float)

        ################## Gradient ascent ##################
        obj_previous = current_objective
        current_objective = objective_mahalanobis(weight_matrix, protected_data, unprotected_data, protected_labels, unprotected_labels, indices_info, lambda_l1_norm)
        print("THIS IS THE CURRENT OBJECTIVE")
        print(current_objective)
        if (current_objective > obj_previous or num_its == 0):
            # Projection successful and improves objective function. Increase learning rate.
            eta *= 1.05
            last_weight_matrix = weight_matrix.copy()
            grad = mahalanobis_derivative(weight_matrix, protected_data, unprotected_data, protected_labels, unprotected_labels, indices_info, lambda_l1_norm)
            # Take gradient step
            weight_matrix += eta * grad

        else:
            # Projection failed or objective function not improved. Shrink learning rate and take last M
            eta *= 0.5
            weight_matrix = last_weight_matrix + eta * grad

        delta = norm(eta * grad, 'fro') / norm(last_weight_matrix, 'fro')
        num_its += 1
        print(num_its)
        if num_its == max_iter or delta < err:
            #Project one last time to make sure matrix is psd
            weight_matrix = (weight_matrix + weight_matrix.T) / 2.0
            weight_matrix = SDProject(weight_matrix).astype(float)
            done = True

    return weight_matrix

