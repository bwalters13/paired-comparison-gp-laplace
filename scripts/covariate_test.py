import numpy as np
import GPyOpt
import pickle as pkl
from tgp.gp_predictor import GPPredictor
from tgp.multiplied_kernel import MultipliedKernel
from tgp.summed_kernel import SummedKernel
from tgp.matern_kernels import MaternKernel32, MaternKernel12
from tgp.rbf_kernel import RBFKernel
from tdata.datasets.oncourt_dataset import OnCourtDataset


dataset = OnCourtDataset()
df = dataset.get_stats_df()

one_year = df[df['year'] >= 2016]
one_year = one_year[one_year['year'] < 2018]

# Prepare the inputs
winners = one_year['winner'].values
losers = one_year['loser'].values
days_since_start = (one_year['start_date'] -
                    one_year['start_date'].min()).dt.days.values

# Make the covariates (surface)
covariates = one_year['surface']

# One-hot-encode
mapping = {'clay': 0, 'grass': 1, 'hard': 2, 'indoor_hard': 3}
cov_nums = [mapping[x] for x in covariates.values]
covariate_array = np.zeros((covariates.shape[0], len(mapping)))
covariate_array[np.arange(covariate_array.shape[0]), cov_nums] = 1

# Add slams, too
# is_slam = one_year['tournament_name'].str.contains(
#     'U.S.Open|Australian Open|Wimbledon|French Open').values
#
# covariate_array = np.concatenate([covariate_array, is_slam.reshape(-1, 1)],
#                                  axis=1)

n_matches = winners.shape[0]
n_surf = len(mapping)


def to_minimise(theta):

    theta = theta[0]

    kernels = list()

    print(theta)
    # Time kernel
    kernels.append(
        SummedKernel(
            [MaternKernel12(np.array([theta[0]]), theta[1], active_dims=[0]),
             MaternKernel32(np.array([theta[2]]), theta[3], active_dims=[0])]
        ))

    # Surface kernel
    kernels.append(RBFKernel(np.array(theta[4:n_surf+4]), 1.,
                   active_dims=[1, 2, 3, 4]))

    # Slam kernel -- currently set variance to 1.
    # TODO: Add more checks around dimensions!
    # kernels.append(RBFKernel(np.array([theta[-1]]), 1, active_dims=[5]))

    kernel = MultipliedKernel(kernels)

    predictor = GPPredictor(kernel)
    predictor.fit(winners, losers, days_since_start,
                  covariates=covariate_array)

    neg_marg_lik = -predictor.calculate_log_marg_lik()

    print(neg_marg_lik)

    return neg_marg_lik


bounds = [{'name': 'l1_t', 'type': 'continuous', 'domain': (0.1, 20.)},
          {'name': 'sd1_t', 'type': 'continuous', 'domain': (0.01, 2.)},
          {'name': 'l2_t', 'type': 'continuous', 'domain': (0.1, 20.)},
          {'name': 'sd2_t', 'type': 'continuous', 'domain': (0.01, 2.)},
          {'name': 'ls_clay', 'type': 'continuous', 'domain': (0.1, 5.)},
          {'name': 'ls_grass', 'type': 'continuous', 'domain': (0.1, 5.)},
          {'name': 'ls_hard', 'type': 'continuous', 'domain': (0.1, 10.)},
          {'name': 'ls_indoor_hard', 'type': 'continuous',
           'domain': (0.1, 10.)}]

max_iter = 100

# result = minimize(to_minimise, theta_init, tol=1)
problem = GPyOpt.methods.BayesianOptimization(to_minimise, bounds)
result = problem.run_optimization(max_iter)

pkl.dump({'best_x': problem.x_opt, 'best_y': problem.fx_opt, 'data': one_year},
         open('gpyopt_results_surface_12plus32.pkl', 'wb'))
