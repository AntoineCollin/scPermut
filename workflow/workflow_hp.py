try :
    from .load import load_runfile
    from .dataset import Dataset
    from .predictor import MLP_Predictor
    from .model import DCA_Permuted,Scanvi,DCA_into_Perm, ScarchesScanvi_LCA
    from .utils import get_optimizer, scanpy_to_input, default_value

    
except ImportError:
    from load import load_runfile
    from dataset import Dataset
    from predictor import MLP_Predictor
    from model import DCA_Permuted,Scanvi
    from utils import get_optimizer, scanpy_to_input, default_value
from dca.utils import str2bool,tuple_to_scalar
import argparse
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from dca.scPermut_subclassing import DANN_AE
from dca.permutation import batch_generator_training_permuted

from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import balanced_accuracy_score,matthews_corrcoef
import time
import yaml
import pickle
import anndata
import pandas as pd
import scanpy as sc
import anndata
import numpy as np 
import os
import sys
import keras
import tensorflow as tf
import neptune

workflow_ID = 'workflow_ID'

dataset = 'dataset'
dataset_name = 'dataset_name'
class_key = 'class_key'
batch_key = 'batch_key'

dataset_normalize = 'dataset_normalize'
filter_min_counts = 'filter_min_counts'
normalize_size_factors = 'normalize_size_factors'
scale_input = 'scale_input'
logtrans_input = 'logtrans_input'
use_hvg = 'use_hvg'
    
model_spec = 'model_spec'
model_name = 'model_name'
ae_type = 'ae_type'
hidden_size = 'hidden_size'
hidden_dropout = 'hidden_dropout'
batchnorm = 'batchnorm'
activation = 'activation'
init = 'init'
batch_removal_weight = 'batch_removal_weight'

model_training_spec = 'model_training_spec'
epochs = 'epochs'
reduce_lr = 'reduce_lr'
early_stop = 'early_stop'
batch_size = 'batch_size'
optimizer = 'optimizer'
verbose = 'verbose'
threads = 'threads'
learning_rate = 'learning_rate'
n_perm = 'n_perm'
permute = 'permute'
change_perm = 'change_perm'
semi_sup = 'semi_sup'
unlabeled_category = 'unlabeled_category'
save_zinb_param = 'save_zinb_param'
use_raw_as_output = 'use_raw_as_output'
contrastive_margin = 'contrastive_margin'
same_class_pct = 'same_class_pct'

dataset_train_split = 'dataset_train_split'
mode = 'mode'
pct_split = 'pct_split'
obs_key = 'obs_key'
n_keep = 'n_keep'
split_strategy = 'split_strategy'
keep_obs = 'keep_obs'
train_test_random_seed = 'train_test_random_seed'
use_TEST = 'use_TEST'
obs_subsample = 'obs_subsample'
    
dataset_fake_annotation = 'dataset_fake_annotation'
make_fake = 'make_fake'
true_celltype = 'true_celltype'
false_celltype = 'false_celltype'
pct_false = 'pct_false'

predictor_spec = 'predictor_spec'
predictor_model = 'predictor_model' 
predict_key = 'predict_key' 
predictor_hidden_sizes = 'predictor_hidden_sizes'
predictor_epochs = 'predictor_epochs'
predictor_batch_size = 'predictor_batch_size'
predictor_activation = 'predictor_activation'

clas_loss_fn = 'clas_loss_fn'
dann_los_fn = 'dann_los_fn'
rec_loss_fn = 'rec_loss_fn'

weight_decay = 'weight_decay'
optimizer_type = 'optimizer_type'

clas_w = 'clas_w'
dann_w = 'dann_w'
rec_w = 'rec_w'


ae_hidden_size = 'ae_hidden_size'
ae_hidden_dropout = 'ae_hidden_dropout'
ae_activation = 'ae_activation'
ae_output_activation = 'ae_output_activation'
ae_init = 'ae_init'
ae_batchnorm = 'ae_batchnorm'
ae_l1_enc_coef = 'ae_l1_enc_coef'
ae_l2_enc_coef = 'ae_l2_enc_coef'
num_classes = 'num_classes'
class_hidden_size = 'class_hidden_size'
class_hidden_dropout = 'class_hidden_dropout'
class_batchnorm = 'class_batchnorm'
class_activation = 'class_activation'
class_output_activation = 'class_output_activation'
num_batches = 'num_batches'
dann_hidden_size = 'dann_hidden_size'
dann_hidden_dropout = 'dann_hidden_dropout'
dann_batchnorm = 'dann_batchnorm'
dann_activation = 'dann_activation'
dann_output_activation = 'dann_output_activation'


class Workflow:
    def __init__(self, run_file, working_dir): 
        '''
        run_file : a dictionary outputed by the function load_runfile
        '''
        self.run_file = run_file
        self.workflow_ID = self.run_file[workflow_ID]
        # dataset identifiers
        self.dataset_name = self.run_file[dataset][dataset_name]
        self.class_key = self.run_file[dataset][class_key]
        self.batch_key = self.run_file[dataset][batch_key]
        # normalization parameters
        self.filter_min_counts = self.run_file[dataset_normalize][filter_min_counts] # TODO :remove, we always want to do that
        self.normalize_size_factors = self.run_file[dataset_normalize][normalize_size_factors]
        self.scale_input = self.run_file[dataset_normalize][scale_input]
        self.logtrans_input = self.run_file[dataset_normalize][logtrans_input]
        self.use_hvg = self.run_file[dataset_normalize][use_hvg]
        # model parameters
        # self.model_name = self.run_file[model_spec][model_name] # TODO : remove, obsolete in the case of DANN_AE
        # self.ae_type = self.run_file[model_spec][ae_type] # TODO : remove, obsolete in the case of DANN_AE
        # self.hidden_size = self.run_file[model_spec][hidden_size] # TODO : remove, obsolete in the case of DANN_AE
        # if type(self.hidden_size) == int: # TODO : remove, obsolete in the case of DANN_AE
        #     self.hidden_size = [2*self.hidden_size, self.hidden_size, 2*self.hidden_size] # TODO : remove, obsolete in the case of DANN_AE
        # self.hidden_dropout = self.run_file[model_spec][hidden_dropout] # TODO : remove, obsolete in the case of DANN_AE
        # if not self.hidden_dropout: # TODO : remove, obsolete in the case of DANN_AE
        #     self.hidden_dropout = 0 
        # self.hidden_dropout = len(self.hidden_size) * [self.hidden_dropout] # TODO : remove, obsolete in the case of DANN_AE
        # self.batchnorm = self.run_file[model_spec][batchnorm] # TODO : remove, obsolete in the case of DANN_AE
        # self.activation = self.run_file[model_spec][activation] # TODO : remove, obsolete in the case of DANN_AE
        # self.init = self.run_file[model_spec][init] # TODO : remove, obsolete in the case of DANN_AE
        # self.batch_removal_weight = self.run_file[model_spec][batch_removal_weight] # TODO : remove, obsolete in the case of DANN_AE
        # model training parameters
        self.epochs = self.run_file[model_training_spec][epochs] # TODO : remove, obsolete in the case of DANN_AE, we use training scheme
        self.reduce_lr = self.run_file[model_training_spec][reduce_lr] # TODO : not implemented yet for DANN_AE 
        self.early_stop = self.run_file[model_training_spec][early_stop] # TODO : not implemented yet for DANN_AE 
        self.batch_size = self.run_file[model_training_spec][batch_size]
        self.optimizer = self.run_file[model_training_spec][optimizer]
        # self.verbose = self.run_file[model_training_spec][verbose] # TODO : not implemented yet for DANN_AE 
        # self.threads = self.run_file[model_training_spec][threads] # TODO : not implemented yet for DANN_AE 
        self.learning_rate = self.run_file[model_training_spec][learning_rate]
        # self.n_perm = self.run_file[model_training_spec][n_perm] # TODO : remove, n_perm is always 1
        # self.permute = self.run_file[model_training_spec][permute] # TODO : remove, obsolete in the case of DANN_AE, handled during training
        # self.change_perm = self.run_file[model_training_spec][change_perm] # TODO : remove, change_perm is always True
        # self.semi_sup = self.run_file[model_training_spec][semi_sup] # TODO : Not yet handled by DANN_AE, the case wwhere unlabeled cells are reconstructed as themselves
        # self.unlabeled_category = self.run_file[model_training_spec][unlabeled_category] # TODO : Not yet handled by DANN_AE, the case wwhere unlabeled cells are reconstructed as themselves
        # self.save_zinb_param = self.run_file[model_training_spec][save_zinb_param] # TODO : remove, obsolete in the case of DANN_AE
        # self.use_raw_as_output = self.run_file[model_training_spec][use_raw_as_output]
        # self.contrastive_margin =self.run_file[model_training_spec][contrastive_margin] # TODO : Not yet handled by DANN_AE, the case where we use constrastive loss
        # self.same_class_pct=self.run_file[model_training_spec][same_class_pct] # TODO : Not yet handled by DANN_AE, the case where we use constrastive loss

        # train test split # TODO : Simplify this, or at first only use the case where data is split according to batch
        self.mode = self.run_file[dataset_train_split][mode]
        self.pct_split = self.run_file[dataset_train_split][pct_split]
        self.obs_key = self.run_file[dataset_train_split][obs_key]
        self.n_keep = self.run_file[dataset_train_split][n_keep]
        self.split_strategy = self.run_file[dataset_train_split][split_strategy]
        self.keep_obs = self.run_file[dataset_train_split][keep_obs]
        self.train_test_random_seed = self.run_file[dataset_train_split][train_test_random_seed]
        # self.use_TEST = self.run_file[dataset_train_split][use_TEST] # TODO : remove, obsolete in the case of DANN_AE
        self.obs_subsample = self.run_file[dataset_train_split][obs_subsample]
        # Create fake annotations
        self.make_fake = self.run_file[dataset_fake_annotation][make_fake]
        self.true_celltype = self.run_file[dataset_fake_annotation][true_celltype]
        self.false_celltype = self.run_file[dataset_fake_annotation][false_celltype]
        self.pct_false = self.run_file[dataset_fake_annotation][pct_false]
        # predictor parameters # TODO : remove, obsolete in the case of DANN_AE, predictor is directly on the model
        # self.predictor_model = self.run_file[predictor_spec][predictor_model]  # TODO : remove, obsolete in the case of DANN_AE
        # self.predict_key = self.run_file[predictor_spec][predict_key] # TODO : remove, obsolete in the case of DANN_AE
        # self.predictor_hidden_sizes = self.run_file[predictor_spec][predictor_hidden_sizes] # TODO : remove, obsolete in the case of DANN_AE
        # self.predictor_epochs = self.run_file[predictor_spec][predictor_epochs] # TODO : remove, obsolete in the case of DANN_AE
        # self.predictor_batch_size = self.run_file[predictor_spec][predictor_batch_size] # TODO : remove, obsolete in the case of DANN_AE
        # self.predictor_activation = self.run_file[predictor_spec][predictor_activation] # TODO : remove, obsolete in the case of DANN_AE
        
        # self.latent_space = anndata.AnnData() # TODO : probably unnecessary, should be handled by logging
        # self.corrected_count = anndata.AnnData() # TODO : probably unnecessary, should be handled by logging
        # self.scarches_combined_emb = anndata.AnnData() # TODO : probably unnecessary, should be handled by logging
        # self.DR_hist = dict() # TODO : probably unnecessary, should be handled by logging
        # self.DR_model = None # TODO : probably unnecessary, should be handled by logging
        
        # self.predicted_class = pd.Series() # TODO : probably unnecessary, should be handled by logging
        # self.pred_hist = dict() # TODO : probably unnecessary, should be handled by logging
        
        # Paths used for the analysis workflow, probably unnecessary
        self.data_dir = working_dir + '/data'
        self.result_dir = working_dir + '/results'
        self.result_path = self.result_dir + f'/result_ID_{self.workflow_ID}'
        self.DR_model_path = self.result_path + '/DR_model'
        self.predictor_model_path = self.result_path + '/predictor_model'
        self.DR_history_path = self.result_path + '/DR_hist.pkl'
        self.pred_history_path = self.result_path + '/pred_hist.pkl'
        self.adata_path = self.result_path + '/latent.h5ad'
        self.corrected_count_path = self.result_path + '/corrected_counts.h5ad'
        self.scarches_combined_emb_path = self.result_path + '/combined_emb.h5ad'
        self.metric_path = self.result_path + '/metrics.csv'
        
        # self.run_log_dir = working_dir + '/logs/run' # TODO : probably unnecessary, should be handled by logging
        # self.run_log_path = self.run_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt' # TODO : probably unnecessary, should be handled by logging
        # self.predict_log_dir = working_dir + '/logs/predicts' # TODO : probably unnecessary, should be handled by logging
        # self.predict_log_path = self.predict_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt' # TODO : probably unnecessary, should be handled by logging
        # self.umap_log_dir = working_dir + '/logs/umap' # TODO : probably unnecessary, should be handled by logging
        # self.umap_log_path = self.umap_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt' # TODO : probably unnecessary, should be handled by logging
        # self.metrics_log_dir = working_dir + '/logs/metrics' # TODO : probably unnecessary, should be handled by logging
        # self.metrics_log_path = self.metrics_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt' # TODO : probably unnecessary, should be handled by logging
        
        self.start_time = time.time()
        self.stop_time = time.time()
        self.runtime_path = self.result_path + '/runtime.txt'

        self.run_done = False 
        self.predict_done = False 
        self.umap_done = False 

        self.dataset = None
        self.model = None
        self.predictor = None
        
        self.training_kwds = {}
        self.network_kwds = {}
    
        ##### TODO : Add to runfile
        
        
        
        self.clas_loss_fn = self.run_file[model_training_spec][clas_loss_fn]
        self.clas_loss_fn = default_value(self.clas_loss_fn, 'MSE')
        self.dann_los_fn = self.run_file[model_training_spec][dann_los_fn]
        self.dann_los_fn = default_value(self.dann_los_fn ,'categorical_crossentropy')
        self.rec_loss_fn = self.run_file[model_training_spec][rec_loss_fn]
        self.rec_loss_fn = default_value(self.rec_loss_fn , 'categorical_crossentropy')
        
        self.weight_decay = self.run_file[model_training_spec][weight_decay]
        self.weight_decay = default_value(self.weight_decay , None)
        self.optimizer_type = self.run_file[model_training_spec][optimizer_type]
        self.optimizer_type = default_value(self.optimizer_type , 'adam')

        self.clas_w = self.run_file[model_training_spec][clas_w]
        self.dann_w = self.run_file[model_training_spec][dann_w]
        self.rec_w = self.run_file[model_training_spec][rec_w]
        
        self.num_classes = None
        self.num_batches = None
        
        self.ae_hidden_size = self.run_file[model_spec][ae_hidden_size]
        self.ae_hidden_size = default_value(self.ae_hidden_size , (128,64,128))
        self.ae_hidden_dropout = self.run_file[model_spec][ae_hidden_dropout]
        self.ae_hidden_dropout = default_value(self.ae_hidden_dropout , None)
        self.ae_activation = self.run_file[model_spec][ae_activation]
        self.ae_activation = default_value(self.ae_activation , "relu")
        self.ae_output_activation = self.run_file[model_spec][ae_output_activation]
        self.ae_output_activation = default_value(self.ae_output_activation , "linear")
        self.ae_init = self.run_file[model_spec][ae_init]
        self.ae_init = default_value(self.ae_init , 'glorot_uniform')
        self.ae_batchnorm = self.run_file[model_spec][ae_batchnorm]
        self.ae_batchnorm = default_value(self.ae_batchnorm , True)
        self.ae_l1_enc_coef = self.run_file[model_spec][ae_l1_enc_coef]
        self.ae_l1_enc_coef = default_value(self.ae_l1_enc_coef , 0)
        self.ae_l2_enc_coef = self.run_file[model_spec][ae_l2_enc_coef]
        self.ae_l2_enc_coef = default_value(self.ae_l2_enc_coef , 0)
        
        self.class_hidden_size = self.run_file[model_spec][class_hidden_size]
        self.class_hidden_size = default_value(self.class_hidden_size , None) # default value will be initialize as [(bottleneck_size + num_classes)/2] once we'll know num_classes
        self.class_hidden_dropout = self.run_file[model_spec][class_hidden_dropout]
        self.class_hidden_dropout = default_value(self.class_hidden_dropout , None) 
        self.class_batchnorm = self.run_file[model_spec][class_batchnorm]
        self.class_batchnorm = default_value(self.class_batchnorm , True)
        self.class_activation = self.run_file[model_spec][class_activation]
        self.class_activation = default_value(self.class_activation , 'relu')
        self.class_output_activation = self.run_file[model_spec][class_output_activation]
        self.class_output_activation = default_value(self.class_output_activation , 'softmax')

        self.dann_hidden_size = self.run_file[model_spec][dann_hidden_size]
        self.dann_hidden_size = default_value(self.dann_hidden_size , None) # default value will be initialize as [(bottleneck_size + num_batches)/2] once we'll know num_classes
        self.dann_hidden_dropout = self.run_file[model_spec][dann_hidden_dropout]
        self.dann_hidden_dropout = default_value(self.dann_hidden_dropout , None)
        self.dann_batchnorm = self.run_file[model_spec][dann_batchnorm]
        self.dann_batchnorm = default_value(self.dann_batchnorm , True)
        self.dann_activation = self.run_file[model_spec][dann_activation]
        self.dann_activation = default_value(self.dann_activation , 'relu')
        self.dann_output_activation =  self.run_file[model_spec][dann_output_activation]
        self.dann_output_activation = default_value(self.dann_output_activation , 'softmax')
        
        self.dann_ae = None

        self.metrics_list = {'balanced_acc' : balanced_accuracy_score, 'mcc' : matthews_corrcoef}

        self.metrics = []

        self.mean_loss_fn = keras.metrics.Mean(name='total loss') # This is a running average : it keeps the previous values in memory when it's called ie computes the previous and current values
        self.mean_clas_loss_fn = keras.metrics.Mean(name='classification loss') 
        self.mean_dann_loss_fn = keras.metrics.Mean(name='dann loss') 
        self.mean_rec_loss_fn = keras.metrics.Mean(name='reconstruction loss') 

        self.training_scheme = None

        self.log_neptune = False
        self.run = None

    def write_metric_log(self):
        open(self.metrics_log_path, 'a').close()
    
    def check_metric_log(self):
        return os.path.isfile(self.metrics_log_path)

    def write_run_log(self):
        open(self.run_log_path, 'a').close()
        
    def write_predict_log(self):
        open(self.predict_log_path, 'a').close()
    
    def write_umap_log(self):
        open(self.umap_log_path, 'a').close()

    
    def check_run_log(self):
        return os.path.isfile(self.run_log_path)
        
    def check_predict_log(self):
        return os.path.isfile(self.predict_log_path)
    
    def check_umap_log(self):
        return os.path.isfile(self.umap_log_path)

    def make_experiment(self, params):
        print(params)
        self.clas_w = params['clas_w']
        self.dann_w = params['dann_w']
        self.rec_w = params['rec_w']

        self.dataset = Dataset(dataset_dir = self.data_dir,
                               dataset_name = self.dataset_name,
                               class_key = self.class_key,
                               batch_key= self.batch_key,
                               filter_min_counts = self.filter_min_counts,
                               normalize_size_factors = self.normalize_size_factors,
                               scale_input = self.scale_input,
                               logtrans_input = self.logtrans_input,
                               use_hvg = self.use_hvg,
                               n_perm = self.n_perm,
                               semi_sup = self.semi_sup,
                               unlabeled_category = self.unlabeled_category)
        self.dataset.load_dataset()
        self.dataset.normalize()
        self.dataset.train_split(mode = self.mode,
                            pct_split = self.pct_split,
                            obs_key = self.obs_key,
                            n_keep = self.n_keep,
                            keep_obs = self.keep_obs,
                            split_strategy = self.split_strategy,
                            obs_subsample = self.obs_subsample,
                            train_test_random_seed = self.train_test_random_seed)
        if self.make_fake:
            self.dataset.fake_annotation(true_celltype=self.true_celltype,
                                    false_celltype=self.false_celltype,
                                    pct_false=self.pct_false,
                                    train_test_random_seed = self.train_test_random_seed)
        print('dataset has been preprocessed')
        self.dataset.create_inputs()
        

        adata_list = {'full': self.dataset.adata,
                      'train': self.dataset.adata_train,
                      'val': self.dataset.adata_val,
                      'test': self.dataset.adata_test}
        
        X_list = {'full': self.dataset.X,
                'train': self.dataset.X_train,
                'val': self.dataset.X_val,
                'test': self.dataset.X_test}
        
        y_list = {'full': self.dataset.y,
                      'train': self.dataset.y_train,
                      'val': self.dataset.y_val,
                      'test': self.dataset.y_test}
        
        batch_list = {'full': self.dataset.batch,
                      'train': self.dataset.batchtrain,
                      'val': self.dataset.batch_val,
                      'test': self.dataset.batch_test}
        
        self.num_classes = len(np.unique(y_list['train']))
        self.num_batches = len(np.unique(batch_list['full']))
        
        bottleneck_size = self.ae_hidden_size[int(len(self.ae_hidden_size)/2)]

        self.class_hidden_size = default_value(self.class_hidden_size , (bottleneck_size + num_classes)/2) # default value [(bottleneck_size + num_classes)/2]
        self.dann_hidden_size = default_value(self.dann_hidden_size , (bottleneck_size + num_batches)/2) # default value [(bottleneck_size + num_batches)/2]

        if self.log_neptune : 
            self.run = neptune.init_run(
                    project="blaireaufurtif/scPermut",
                    api_token="eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiJiMmRkMWRjNS03ZGUwLTQ1MzQtYTViOS0yNTQ3MThlY2Q5NzUifQ==",
)           
            for k in self.run_file:
                for par,val in self.run_file[k].items():
                    self.run[f"parameters/{k}/{par}"] = val


        self.dann_ae = DANN_AE(ae_hidden_size=self.ae_hidden_size,
                        ae_hidden_dropout=self.ae_hidden_dropout,
                        ae_activation=self.ae_activation,
                        ae_output_activation=self.ae_output_activation,
                        ae_init=self.ae_init,
                        ae_batchnorm=self.ae_batchnorm,
                        ae_l1_enc_coef=self.ae_l1_enc_coef,
                        ae_l2_enc_coef=self.ae_l2_enc_coef,
                        num_classes=self.num_classes,
                        class_hidden_size=self.class_hidden_size,
                        class_hidden_dropout=self.class_hidden_dropout,
                        class_batchnorm=self.class_batchnorm,
                        class_activation=self.class_activation,
                        class_output_activation=self.class_output_activation,
                        num_batches=self.num_batches,
                        dann_hidden_size=self.dann_hidden_size,
                        dann_hidden_dropout=self.dann_hidden_dropout,
                        dann_batchnorm=self.dann_batchnorm,
                        dann_activation=self.dann_activation,
                        dann_output_activation=self.dann_output_activation)

        self.optimizer = get_optimizer(self.learning_rate, self.weight_decay, self.optimizer_type)
        self.rec_loss_fn, self.clas_loss_fn, self.dann_los_fn = self.get_losses() # redundant
        self.training_scheme = self.get_scheme(self.training_scheme)

        history = self.train_scheme(training_scheme=self.training_scheme,
                                    verbose = False,
                                    ae = self.dann_ae,
                                     adata_list= adata_list,
                                     X_list= X_list,
                                     y_list= y_list,
                                     batch_list= batch_list,
                                     optimizer= self.optimizer,
                                     clas_loss_fn = self.clas_loss_fn,
                                     dann_los_fn = self.dann_loss_fn,
                                     rec_loss_fn = self.rec_los_fn)
        
        if self.log_neptune:
            for group in ['full', 'train', 'val', 'test']:
                _, clas, dann, rec = self.dann_ae.predict(scanpy_to_input(adata_list[group],['size_factors'])).values()
                clas = np.eye(clas.shape[1])[np.argmax(clas, axis=1)]
                for metric in self.metrics_list: # only classification metrics ATM
                    self.run[f"evaluation/{group}/{metric}"] = self.metrics_list[metric](y_list[group].argmax(axis=1), clas.argmax(axis=1))

        _, clas, dann, rec = self.dann_ae.predict(scanpy_to_input(adata_list['val'],['size_factors'])).values()
        clas = np.eye(clas.shape[1])[np.argmax(clas, axis=1)]
        opt_metric = self.metrics_list['mcc'](y_list['val'].argmax(axis=1), clas.argmax(axis=1)) # We retrieve the last metric of interest
        if self.log_neptune:
            self.run.stop()
        return opt_metric
        
    def train_scheme(self, 
                    training_scheme, 
                    verbose = True ,
                    **loop_params):
        """
        training scheme : dictionnary explaining the succession of strategies to use as keys with the corresponding number of epochs and use_perm as values.
                        ex :  training_scheme_3 = {"warmup_dann" : (10, False), "full_model":(10, False)}
        """
        history = {'train': {}, 'val': {}} # initialize history
        for group in history.keys():
            history[group] = {'total_loss':[],
                            'clas_loss':[],
                            'dann_loss':[],
                            'rec_loss':[]}
            for m in self.metrics_list:
                history[group][m] = []

        if self.log_neptune:
            for group in history:
                for par,val in self.run_file[group].items():
                    self.run[f"training/{group}/{par}"] = [] 
        i = 0
        
        total_epochs = np.sum([n_epochs for _, n_epochs, _ in training_scheme])
        running_epoch = 0
        
        for (strategy, n_epochs, use_perm) in training_scheme:
            if verbose :
                print(f"Step number {i}, running {strategy} strategy with permuation = {use_perm} for {n_epochs} epochs")
                time_in = time.time()

                # Early stopping for those strategies only
            if strategy in  ['full_model', 'classifier_branch']:
                wait = 0
                best_epoch = 0
                es_best = np.inf # initialize early_stopping
                patience = 2
                monitored = 'mcc'

            for epoch in range(1, n_epochs+1):
                running_epoch +=1
                print(f"Epoch {running_epoch}/{total_epochs}, Current strat Epoch {epoch}/{n_epochs}")
                history, bot, cl, d ,re = self.training_loop(history=history,training_strategy=strategy,use_perm=use_perm, **loop_params)
                
                if self.log_neptune:
                    for group in history:
                        for par,value in self.run_file[group].items():
                            self.run[f"training/{group}/{par}"].append(value[-1])

                # Early stopping
                wait += 1
                monitored_value = history['val'][monitored][-1]
                
                if monitored_value < es_best:
                    best_epoch = epoch
                    es_best = monitored_value
                    wait = 0
                    best_model = self.dann_ae.get_weights()
                if wait >= patience:
                    print(f'Early stopping at epoch {best_epoch}, restoring model parameters from this epoch')
                    self.dann_ae.set_weights(best_model)
                    break

            if verbose:
                time_out = time.time()
                print(f"Epoch duration : {time_out - time_in} s")

        # dann_ae.set_weights(best_weights)
        return history
    

    def training_loop(self, history,
                            ae,
                            adata_list,
                            X_list,
                            y_list,
                            batch_list,
                            optimizer,
                            clas_loss_fn,
                            dann_los_fn,
                            rec_loss_fn,
                            use_perm=None, 
                            training_strategy="full_model"):
        '''
        A consolidated training loop function that covers common logic used in different training strategies.
        
        training_strategy : one of ["full", "warmup_dann", "warmup_dann_no_rec", "classifier_branch", "permutation_only"]
            - full_model : trains the whole model, optimizing the 3 losses (reconstruction, classification, anti batch discrimination ) at once
            - warmup_dann : trains the dann, encoder and decoder with reconstruction (no permutation because unsupervised), maximizing the dann loss and minimizing the reconstruction loss
            - warmup_dann_no_rec : trains the dann and encoder without reconstruction, maximizing the dann loss only.
            - dann_with_ae : same as warmup dann but with permutation. Separated in two strategies because this one is supervised
            - classifier_branch : trains the classifier branch only, without the encoder. Use to fine tune the classifier once training is over
            - permutation_only : trains the autoencoder with permutations, optimizing the reconstruction loss without the classifier
        use_perm : True by default except form "warmup_dann" training strategy. Note that for training strategies that don't involve the reconstruction, this parameter has no impact on training
        '''
        
        self.unfreeze_all(ae) # resetting freeze state
        if training_strategy == "full_model":
            adata = adata_list['train']
        elif training_strategy == "warmup_dann":
            adata = adata_list['full'] # unsupervised setting
            ae.classifier.trainable = False # Freezing classifier just to be sure but should not be necessary since gradient won't be propagating in this branch
            use_perm = False # no permutation for warming up the dann. No need to specify it in the no rec version since we don't reconstruct
        elif training_strategy == "warmup_dann_no_rec":
            adata = adata_list['full']
            self.freeze_block(ae, 'all_but_dann')
        elif training_strategy == "dann_with_ae":
            adata = adata_list['train']
            ae.classifier.trainable = False
            use_perm = True
        elif training_strategy == "classifier_branch":
            adata = adata_list['train']
            self.freeze_block(ae, 'all_but_classifier_branch') # traning only classifier branch
        elif training_strategy == "permutation_only":
            adata = adata_list['train']
            self.freeze_block(ae, 'all_but_autoencoder')
        
        if not use_perm:
            use_perm = True

        batch_generator = batch_generator_training_permuted(adata, class_key=self.class_key, batch_key=self.batch_key,
                                                            ret_input_only=False, batch_size=batch_size, n_perm=1, use_raw_as_output=False, use_perm=use_perm)
        n_obs = adata.n_obs
        steps = n_obs // batch_size + 1
        n_steps = steps
        n_samples = 0

        self.mean_loss_fn.reset_state()
        self.mean_clas_loss_fn.reset_state()
        self.mean_dann_loss_fn.reset_state()
        self.mean_rec_loss_fn.reset_state()

        for step in range(1, n_steps + 1):
            input_batch, output_batch = next(batch_generator)
            X_batch, sf_batch = input_batch.values()
            clas_batch, dann_batch, rec_batch = output_batch.values()

            with tf.GradientTape() as tape:
                enc, clas, dann, rec = ae(input_batch, training=True).values()
                clas_loss = tf.reduce_mean(clas_loss_fn(clas_batch, clas))
                dann_loss = tf.reduce_mean(dann_los_fn(dann_batch, dann))
                rec_loss = tf.reduce_mean(rec_loss_fn(rec_batch, rec))
                if training_strategy == "full_model":
                    loss = tf.add_n([self.clas_w * clas_loss] + [self.dann_w * dann_loss] + [self.rec_w * rec_loss] + ae.losses)
                elif training_strategy == "warmup_dann":
                    loss = tf.add_n([self.dann_w * dann_loss] + [self.rec_w * rec_loss] + ae.losses)
                elif training_strategy == "warmup_dann_no_rec":
                    loss = tf.add_n([self.dann_w * dann_loss] + ae.losses)
                elif training_strategy == "dann_with_ae":
                    loss = tf.add_n([self.dann_w * dann_loss] + [self.rec_w * rec_loss] + ae.losses)
                elif training_strategy == "classifier_branch":
                    loss = tf.add_n([self.clas_w * clas_loss] + ae.losses)
                elif training_strategy == "permutation_only":
                    loss = tf.add_n([self.rec_w * rec_loss] + ae.losses)

            n_samples += enc.shape[0]
            gradients = tape.gradient(loss, ae.trainable_variables)
            optimizer.apply_gradients(zip(gradients, ae.trainable_variables))

            mean_loss = self.mean_loss_fn(loss)
            mean_clas_loss = self.mean_clas_loss_fn(clas_loss)
            mean_dann_loss = self.mean_dann_loss_fn(dann_loss)
            mean_rec_loss = self.mean_rec_loss_fn(rec_loss)

            self.print_status_bar(n_samples, n_obs, [self.mean_loss_fn, self.mean_clas_loss_fn, self.mean_dann_loss_fn, self.mean_rec_loss_fn], self.metrics)
        history, _, clas, dann, rec = self.evaluation_pass_epoch_end(history, ae, adata_list, X_list, y_list, batch_list, clas_loss_fn, dann_los_fn, rec_loss_fn)

        return history, _, clas, dann, rec

    def evaluation_pass(self,history, ae, adata_list, X_list, y_list, batch_list, clas_loss_fn, dann_los_fn, rec_loss_fn):
        '''
        evaluate model and logs metrics. Depending on "on parameter, computes it on train and val or train,val and test.

        on : "epoch_end" to evaluate on train and val, "training_end" to evaluate on train, val and "test".
        '''
        for group in ['train', 'val']: # evaluation round
            _, clas, dann, rec = ae.predict(scanpy_to_input(adata_list[group],['size_factors'])).values()
    #         return _, clas, dann, rec 
            clas_loss = tf.reduce_mean(clas_loss_fn(y_list[group], clas))
            history[group]['clas_loss'] += [clas_loss.numpy()]
            dann_loss = tf.reduce_mean(dann_los_fn(batch_list[group], dann))
            history[group]['dann_loss'] += [dann_loss.numpy()]
            rec_loss = tf.reduce_mean(rec_loss_fn(X_list[group], rec))
            history[group]['rec_loss'] += [rec_loss.numpy()]
            history[group]['total_loss'] += [tf.add_n([self.clas_w * clas_loss] + [self.dann_w * dann_loss] + [self.rec_w * rec_loss] + ae.losses).numpy()]
            
            clas = np.eye(clas.shape[1])[np.argmax(clas, axis=1)]
            for metric in self.metrics_list: # only classification metrics ATM
                history[group][metric] += [self.metrics_list[metric](y_list[group].argmax(axis=1), clas.argmax(axis=1))] # y_list are onehot encoded
        return history, _, clas, dann, rec
    
    def freeze_layers(self, ae, layers_to_freeze):
        '''
        Freezes specified layers in the model.
        
        ae: Model to freeze layers in.
        layers_to_freeze: List of layers to freeze.
        '''
        for layer in layers_to_freeze:
            layer.trainable = False


    def freeze_block(self, ae, strategy):
        if strategy == "all_but_classifier_branch":
            layers_to_freeze = [ae.dann_discriminator, ae.enc, ae.dec, ae.ae_output_layer]
        elif strategy == "all_but_classifier":
            layers_to_freeze = [ae.dann_discriminator, ae.dec, ae.ae_output_layer]
        elif strategy == "all_but_dann_branch":
            layers_to_freeze = [ae.classifier, ae.dec, ae.ae_output_layer, ae.enc]
        elif strategy == "all_but_dann":
            layers_to_freeze = [ae.classifier, ae.dec, ae.ae_output_layer]
        elif strategy == "all_but_autoencoder":
            layers_to_freeze = [ae.classifier, ae.dann_discriminator]
        else:
            raise ValueError("Unknown freeze strategy: " + strategy)
        
        self.freeze_layers(ae, layers_to_freeze)
        

    def freeze_all(self, ae):
        for l in ae.layers:
            l.trainable = False

    def unfreeze_all(self, ae):
        for l in ae.layers:
            l.trainable = True
    

    def get_scheme(self):
        if self.training_scheme == 'training_scheme_1':
            self.training_scheme = [("warmup_dann", self.warmup_epoch, False),
                                  ("full_model", 100, False)] # This will end with a callback
        if self.training_scheme == 'training_scheme_2':
            self.training_scheme = [("warmup_dann", self.warmup_epoch, False),
                                ("permutation_only", 30, True),
                                ("classifier_branch", 100, False)] # This will end with a callback
        return self.training_scheme
        
            

    def get_losses(self):
        if self.rec_loss_fn == 'MSE':
            self.rec_loss_fn = tf.keras.losses.mean_squared_error
        else:
            print(self.rec_loss_fn + ' loss not supported for rec')
        if self.clas_loss_fn == 'categorical_crossentropy':
            self.clas_loss_fn = tf.keras.losses.categorical_crossentropy
        else:
            print(self.clas_loss_fn + ' loss not supported for classif')
        if self.dann_los_fn == 'categorical_crossentropy':
            self.dann_los_fn = tf.keras.losses.categorical_crossentropy
        else:
            print(self.dann_los_fn + ' loss not supported for dann')
        return self.rec_loss_fn,self.clas_loss_fn,self.dann_los_fn
    

    def print_status_bar(iteration, total, loss, metrics=None):
        metrics = ' - '.join(['{}: {:.4f}'.format(m.name, m.result())
                            for m in loss + (metrics or [])])
        
        end = "" if iteration < total else "\n"
    #     print(f"{iteration}/{total} - "+metrics ,end="\r")
    #     print(f"\r{iteration}/{total} - " + metrics, end=end)
        print("\r{}/{} - ".format(iteration,total) + metrics, end =end)


    def compute_prediction_only(self):
        self.latent_space = sc.read_h5ad(self.adata_path)
        if self.predictor_model == 'MLP':
            self.predictor = MLP_Predictor(latent_space = self.latent_space,
                                           predict_key = self.predict_key,
                                           predictor_hidden_sizes = self.predictor_hidden_sizes,
                                           predictor_epochs = self.predictor_epochs,
                                           predictor_batch_size = self.predictor_batch_size,
                                           predictor_activation = self.predictor_activation,
                                           unlabeled_category = self.unlabeled_category)
            self.predictor.preprocess_one_hot()
            self.predictor.build_predictor()
            self.predictor.train_model()
            self.predictor.predict_on_test()
            self.pred_hist = self.predictor.train_history
            self.predicted_class = self.predictor.y_pred
            self.latent_space.obs[f'{self.class_key}_pred'] = self.predicted_class
            self.predict_done = True
        
    
    def compute_umap(self):
        sc.tl.pca(self.latent_space)
        sc.pp.neighbors(self.latent_space, use_rep = 'X', key_added = f'neighbors_{self.model_name}')
        sc.pp.neighbors(self.latent_space, use_rep = 'X_pca', key_added = 'neighbors_pca')
        sc.tl.umap(self.latent_space, neighbors_key = f'neighbors_{self.model_name}')
        print(self.latent_space)
        print(self.adata_path)
        self.latent_space.write(self.adata_path)
        self.write_umap_log()
        self.umap_done = True

    def predict_knn_classifier(self, n_neighbors = 50, embedding_key=None, return_clustering = False):
        adata_train = self.latent_space[self.latent_space.obs['TRAIN_TEST_split'] == 'train']
        adata_train = adata_train[adata_train.obs[self.class_key] != self.unlabeled_category]
       
        knn_class = KNeighborsClassifier(n_neighbors = n_neighbors)
        
        if embedding_key:
            knn_class.fit(adata_train.obsm[embedding_key], adata_train.obs[self.class_key])        
            pred_clusters = knn_class.predict(self.latent_space.X)
            if return_clustering:
                return pred_clusters
            else:
                self.latent_space.obs[f'{self.class_key}_{embedding_key}_knn_classifier{n_neighbors}_pred'] = pred_clusters
        else :
            knn_class.fit(adata_train.X, adata_train.obs[self.class_key])
            pred_clusters = knn_class.predict(self.latent_space.X)
            if return_clustering:
                return pred_clusters
            else:
                self.latent_space.obs[f'{self.class_key}_knn_classifier{n_neighbors}_pred'] = pred_clusters


    def predict_kmeans(self, embedding_key=None):
        n_clusters = len(np.unique(self.latent_space.obs[self.class_key]))

        kmeans = KMeans(n_clusters = n_clusters)
        
        if embedding_key:
            kmeans.fit_predict(self.latent_space.obsm[embedding_key])
            self.latent_space.obs[f'{embedding_key}_kmeans_pred'] = kmeans.predict(self.latent_space.obsm[embedding_key])
        else :
            kmeans.fit_predict(self.latent_space.X)
            self.latent_space.obs[f'kmeans_pred'] = kmeans.predict(self.latent_space.X)

    def compute_leiden(self, **kwargs):
        sc.tl.leiden(self.latent_space, key_added = 'leiden_latent', neighbors_key = f'neighbors_{self.model_name}', **kwargs)
    
    def save_results(self):
        if not os.path.isdir(self.result_path):
            os.makedirs(self.result_path)
        try:
            self.latent_space.write(self.adata_path)
        except NotImplementedError:
            self.latent_space.uns['runfile_dict'] = dict() # Quick workaround
            self.latent_space.write(self.adata_path)
#         self.model.save_net(self.DR_model_path)
#         if self.predictor_model:
#             self.predictor.save_model(self.predictor_model_path)
        if self.scarches_combined_emb:
            self.scarches_combined_emb.write(self.scarches_combined_emb_path)
        if self.save_zinb_param:
            if self.corrected_count :
                self.corrected_count.write(self.corrected_count_path)
        if self.model_name != 'scanvi':
            if self.DR_hist:
                with open(self.DR_history_path, 'wb') as file_pi:
                    pickle.dump(self.DR_hist.history, file_pi)
        if self.predict_done and self.pred_hist:
            with open(self.pred_history_path, 'wb') as file_pi:
                pickle.dump(self.pred_hist.history, file_pi)
        if self.run_done:
            self.write_run_log()
        if self.predict_done:
            self.write_predict_log()
        if self.umap_done:
            self.write_umap_log()
        if not os.path.exists(self.result_path):
            metric_series = pd.DataFrame(index = [self.workflow_ID], data={'workflow_ID':pd.Series([self.workflow_ID], index = [self.workflow_ID])})
            metric_series.to_csv(self.metric_path)
        if not os.path.exists(self.runtime_path):
            with open(self.runtime_path, 'w') as f:
                f.write(str(self.stop_time - self.start_time))


    def load_results(self):
        if os.path.isdir(self.result_path):
            try:
                self.latent_space = sc.read_h5ad(self.adata_path)
            except OSError as e:
                print(e)
                print(f'failed to load {self.workflow_ID}')
                return self.workflow_ID # Returns the failed id
        if self.check_run_log():
            self.run_done = True
        if self.check_predict_log():
            self.predict_done = True
        if self.check_umap_log():
            self.umap_done = True
            
    def load_corrected(self):
        if os.path.isdir(self.result_path):
            self.corrected_count = sc.read_h5ad(self.corrected_count_path)
            self.corrected_count.obs = self.latent_space.obs
            self.corrected_count.layers['X_dca_dropout'] = self.corrected_count.obsm['X_dca_dropout']
            self.corrected_count.layers['X_dca_dispersion'] = self.corrected_count.obsm['X_dca_dispersion']
            self.corrected_count.obsm['X_umap'] = self.latent_space.obsm['X_umap']

    def __str__(self):
        return str(self.run_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # parser.add_argument('--run_file', type = , default = , help ='')
    # parser.add_argument('--workflow_ID', type = , default = , help ='')
    parser.add_argument('--dataset_name', type = str, default = 'disco_ajrccm_downsampled', help ='Name of the dataset to use, should indicate a raw h5ad AnnData file')
    parser.add_argument('--class_key', type = str, default = 'celltype_lv2_V3', help ='Key of the class to classify')
    parser.add_argument('--batch_key', type = str, default = 'manip', help ='Key of the batches')
    parser.add_argument('--filter_min_counts', type=str2bool, nargs='?',const=True, default=True, help ='Filters genes with <1 counts')# TODO :remove, we always want to do that
    parser.add_argument('--normalize_size_factors', type=str2bool, nargs='?',const=True, default=True, help ='Weither to normalize dataset or not')
    parser.add_argument('--scale_input', type=str2bool, nargs='?',const=True, default=True, help ='Weither to scale input the count values')
    parser.add_argument('--logtrans_input', type=str2bool, nargs='?',const=True, default=True, help ='Weither to log transform count values')
    parser.add_argument('--use_hvg', type=int, nargs='?', const=10000, default=None, help = "Number of hvg to use. If no tag, don't use hvg.")
    # parser.add_argument('--reduce_lr', type = , default = , help ='')
    # parser.add_argument('--early_stop', type = , default = , help ='')
    parser.add_argument('--batch_size', type = int, nargs='?', default = 128, help ='Training batch size')
    # parser.add_argument('--verbose', type = , default = , help ='')
    # parser.add_argument('--threads', type = , default = , help ='')
    parser.add_argument('--mode', type = str, default = 'percentage', help ='Train test split mode to be used by Dataset.train_split')
    parser.add_argument('--pct_split', type = float,nargs='?', default = 0.9, help ='')
    parser.add_argument('--obs_key', type = str,nargs='?', default = 'manip', help ='')
    parser.add_argument('--n_keep', type = int,nargs='?', default = None, help ='')
    parser.add_argument('--split_strategy', type = str,nargs='?', default = None, help ='')
    parser.add_argument('--keep_obs', type = str,nargs='?',default = None, help ='')
    parser.add_argument('--train_test_random_seed', type = float,nargs='?', default = 0, help ='')
    parser.add_argument('--obs_subsample', type = str,nargs='?', default = None, help ='')
    parser.add_argument('--make_fake', type=str2bool, nargs='?',const=False, default=False, help ='')
    parser.add_argument('--true_celltype', type = str,nargs='?', default = None, help ='')
    parser.add_argument('--false_celltype', type = str,nargs='?', default = None, help ='')
    parser.add_argument('--pct_false', type = float,nargs='?', default = None, help ='')
    parser.add_argument('--clas_loss_fn', type = str,nargs='?', choices = ['MSE'], default = 'MSE' , help ='Loss of the classification branch')
    parser.add_argument('--dann_los_fn', type = str,nargs='?', choices = ['categorical_crossentropy'], default ='categorical_crossentropy', help ='Loss of the DANN branch')
    parser.add_argument('--rec_loss_fn', type = str,nargs='?', choices = ['categorical_crossentropy'], default ='categorical_crossentropy', help ='Reconstruction loss of the autoencoder')
    parser.add_argument('--weight_decay', type = float,nargs='?', default = 1e-4, help ='Weight decay applied by th optimizer')
    parser.add_argument('--learning_rate', type = float,nargs='?', default = 0.001, help ='Starting learning rate for training')
    parser.add_argument('--optimizer_type', type = str, nargs='?',choices = ['adam','adamw','rmsprop'], default = 'adam' , help ='Name of the optimizer to use')
    parser.add_argument('--clas_w', type = float,nargs='?', default = 0.1, help ='Wight of the classification loss')
    parser.add_argument('--dann_w', type = float,nargs='?', default = 0.1, help ='Wight of the DANN loss')
    parser.add_argument('--rec_w', type = float,nargs='?', default = 0.8, help ='Wight of the reconstruction loss')
    parser.add_argument('--ae_hidden_size', type = int,nargs='+', default = [128,64,128], help ='Hidden sizes of the successive ae layers')
    parser.add_argument('--ae_hidden_dropout', type =float, nargs='?', default = None, help ='')
    parser.add_argument('--ae_activation', type = str ,nargs='?', default = 'relu' , help ='')
    parser.add_argument('--ae_output_activation', type = str,nargs='?', default = 'linear', help ='')
    parser.add_argument('--ae_init', type = str,nargs='?', default = 'glorot_uniform', help ='')
    parser.add_argument('--ae_batchnorm', type=str2bool, nargs='?',const=True, default=True , help ='')
    parser.add_argument('--ae_l1_enc_coef', type = float,nargs='?', default = None, help ='')
    parser.add_argument('--ae_l2_enc_coef', type = float,nargs='?', default = None, help ='')
    parser.add_argument('--class_hidden_size', type = int,nargs='+', default = [64], help ='Hidden sizes of the successive classification layers')
    parser.add_argument('--class_hidden_dropout', type =float, nargs='?', default = None, help ='')
    parser.add_argument('--class_batchnorm', type=str2bool, nargs='?',const=True, default=True , help ='')
    parser.add_argument('--class_activation', type = str ,nargs='?', default = 'relu' , help ='')
    parser.add_argument('--class_output_activation', type = str,nargs='?', default = 'softmax', help ='')
    parser.add_argument('--dann_hidden_size', type = int,nargs='?', default = [64], help ='')
    parser.add_argument('--dann_hidden_dropout', type =float, nargs='?', default = None, help ='')
    parser.add_argument('--dann_batchnorm', type=str2bool, nargs='?',const=True, default=True , help ='')
    parser.add_argument('--dann_activation', type = str ,nargs='?', default = 'relu' , help ='')
    parser.add_argument('--dann_output_activation', type = str,nargs='?', default = 'softmax', help ='')
    parser.add_argument('--training_scheme', type = str,nargs='?', default = 'training_scheme_1', help ='')
    parser.add_argument('--warmup_epoch', type = int,nargs='?', default = 30, help ='')
    parser.add_argument('--log_neptune', type=str2bool, nargs='?',const=True, default=True , help ='')
    
    run_file = parser.parse_args()
    working_dir = ...
    workflow = Workflow(run_file=run_file, working_dir=working_dir)
    workflow.make_experiment(params)
