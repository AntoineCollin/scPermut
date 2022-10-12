try :
    from .load import load_runfile
    from .dataset import Dataset
    from .predictor import MLP_Predictor
    from .model import DCA_Permuted,Scanvi,DCA_into_Perm, ScarchesScanvi_LCA
except ImportError:
    from load import load_runfile
    from dataset import Dataset
    from predictor import MLP_Predictor
    from model import DCA_Permuted,Scanvi

import yaml
import pickle
import anndata
import pandas as pd
import scanpy as sc
import anndata
import numpy as np 
import os

workflow_ID = 'workflow_ID'

dataset = 'dataset'
dataset_name = 'dataset_name'
class_key = 'class_key'

dataset_normalize = 'dataset_normalize'
filter_min_counts = 'filter_min_counts'
normalize_size_factors = 'normalize_size_factors'
scale_input = 'scale_input'
logtrans_input = 'logtrans_input'
    
model_spec = 'model_spec'
model_name = 'model_name'
ae_type = 'ae_type'
hidden_size = 'hidden_size'
hidden_dropout = 'hidden_dropout'
batchnorm = 'batchnorm'
activation = 'activation'
init = 'init'

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

class Workflow:
    def __init__(self, yaml_name, working_dir):
        run_file = load_runfile(yaml_name)
        self.workflow_ID = run_file[workflow_ID]
        # dataset identifiers
        self.dataset_name = run_file[dataset][dataset_name]
        self.class_key = run_file[dataset][class_key]
        # normalization parameters
        self.filter_min_counts = run_file[dataset_normalize][filter_min_counts]
        self.normalize_size_factors = run_file[dataset_normalize][normalize_size_factors]
        self.scale_input = run_file[dataset_normalize][scale_input]
        self.logtrans_input = run_file[dataset_normalize][logtrans_input]
        # model parameters
        self.model_name = run_file[model_spec][model_name]
        self.ae_type = run_file[model_spec][ae_type]
        self.hidden_size = run_file[model_spec][hidden_size]
        self.hidden_size = (2*self.hidden_size, self.hidden_size, 2*self.hidden_size)
        self.hidden_dropout = run_file[model_spec][hidden_dropout]
        self.batchnorm = run_file[model_spec][batchnorm]
        self.activation = run_file[model_spec][activation]
        self.init = run_file[model_spec][init]
        # model training parameters
        self.epochs = run_file[model_training_spec][epochs]
        self.reduce_lr = run_file[model_training_spec][reduce_lr]
        self.early_stop = run_file[model_training_spec][early_stop]
        self.batch_size = run_file[model_training_spec][batch_size]
        self.optimizer = run_file[model_training_spec][optimizer]
        self.verbose = run_file[model_training_spec][verbose]
        self.threads = run_file[model_training_spec][threads]
        self.learning_rate = run_file[model_training_spec][learning_rate]
        self.n_perm = run_file[model_training_spec][n_perm]
        self.permute = run_file[model_training_spec][permute]
        self.change_perm = run_file[model_training_spec][change_perm]
        self.semi_sup = run_file[model_training_spec][semi_sup]
        self.unlabeled_category = run_file[model_training_spec][unlabeled_category]
        self.save_zinb_param = run_file[model_training_spec][save_zinb_param]
        self.use_raw_as_output = run_file[model_training_spec][use_raw_as_output]
        self.contrastive_margin =run_file[model_training_spec][contrastive_margin]
        self.same_class_pct=run_file[model_training_spec][same_class_pct]

        # train test split
        self.mode = run_file[dataset_train_split][mode]
        self.pct_split = run_file[dataset_train_split][pct_split]
        self.obs_key = run_file[dataset_train_split][obs_key]
        self.n_keep = run_file[dataset_train_split][n_keep]
        self.keep_obs = run_file[dataset_train_split][keep_obs]
        self.train_test_random_seed = run_file[dataset_train_split][train_test_random_seed]
        self.use_TEST = run_file[dataset_train_split][use_TEST]
        self.obs_subsample = run_file[dataset_train_split][obs_subsample]
        # Create fake annotations
        self.make_fake = run_file[dataset_fake_annotation][make_fake]
        self.true_celltype = run_file[dataset_fake_annotation][true_celltype]
        self.false_celltype = run_file[dataset_fake_annotation][false_celltype]
        self.pct_false = run_file[dataset_fake_annotation][pct_false]
        # predictor parameters
        self.predictor_model = run_file[predictor_spec][predictor_model]
        self.predict_key = run_file[predictor_spec][predict_key]
        self.predictor_hidden_sizes = run_file[predictor_spec][predictor_hidden_sizes]
        self.predictor_epochs = run_file[predictor_spec][predictor_epochs]
        self.predictor_batch_size = run_file[predictor_spec][predictor_batch_size]
        self.predictor_activation = run_file[predictor_spec][predictor_activation]
        
        self.latent_space = anndata.AnnData()
        self.corrected_count = anndata.AnnData()
        self.scarches_combined_emb = anndata.AnnData()
        self.DR_hist = dict()
        self.DR_model = None
        
        self.predicted_class = pd.Series()
        self.pred_hist = dict()
        
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
        
        self.run_log_dir = working_dir + '/logs/run'
        self.run_log_path = self.run_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt'
        self.predict_log_dir = working_dir + '/logs/predicts'
        self.predict_log_path = self.predict_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt'
        self.umap_log_dir = working_dir + '/logs/umap'
        self.umap_log_path = self.umap_log_dir + f'/workflow_ID_{self.workflow_ID}_DONE.txt'

        
        self.run_done = False
        self.predict_done = False
        self.umap_done = False

        self.dataset = None
        self.model = None
        self.predictor = None
        
        self.training_kwds = {}
        self.network_kwds = {}
    
    
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

    def load_dataset(self):
        self.dataset = Dataset(dataset_dir = self.data_dir,
                               dataset_name = self.dataset_name,
                               class_key = self.class_key,
                               filter_min_counts = self.filter_min_counts,
                               normalize_size_factors = self.normalize_size_factors,
                               scale_input = self.scale_input,
                               logtrans_input = self.logtrans_input,
                               n_perm = self.n_perm,
                               semi_sup = self.semi_sup,
                               unlabeled_category = self.unlabeled_category)
    
    def make_experiment(self):
        self.dataset = Dataset(dataset_dir = self.data_dir,
                               dataset_name = self.dataset_name,
                               class_key = self.class_key,
                               filter_min_counts = self.filter_min_counts,
                               normalize_size_factors = self.normalize_size_factors,
                               scale_input = self.scale_input,
                               logtrans_input = self.logtrans_input,
                               n_perm = self.n_perm,
                               semi_sup = self.semi_sup,
                               unlabeled_category = self.unlabeled_category)
        if self.model_name == 'dca_permuted':
            print(self.model_name)
            self.model = DCA_Permuted(ae_type = self.ae_type,
                                     hidden_size = self.hidden_size,
                                     hidden_dropout = self.hidden_dropout, 
                                     batchnorm = self.batchnorm, 
                                     activation = self.activation, 
                                     init = self.init,
                                     epochs = self.epochs,
                                     reduce_lr = self.reduce_lr, 
                                     early_stop = self.early_stop, 
                                     batch_size = self.batch_size, 
                                     optimizer = self.optimizer,
                                     verbose = self.verbose,
                                     threads = self.threads, 
                                     learning_rate = self.learning_rate,
                                     training_kwds = self.training_kwds,
                                     network_kwds = self.network_kwds, 
                                     n_perm = self.n_perm, 
                                     permute = self.permute,
                                     change_perm = self.change_perm,
                                     class_key = self.class_key,
                                     unlabeled_category = self.unlabeled_category,
                                     use_raw_as_output=self.use_raw_as_output,
                                     contrastive_margin = self.contrastive_margin,
                                     same_class_pct = self.same_class_pct)
            
        if self.model_name == 'dca_into_perm':    
            self.model = DCA_into_Perm(ae_type = self.ae_type,
                                     hidden_size = self.hidden_size,
                                     hidden_dropout = self.hidden_dropout, 
                                     batchnorm = self.batchnorm, 
                                     activation = self.activation, 
                                     init = self.init,
                                     epochs = self.epochs,
                                     reduce_lr = self.reduce_lr, 
                                     early_stop = self.early_stop, 
                                     batch_size = self.batch_size, 
                                     optimizer = self.optimizer,
                                     verbose = self.verbose,
                                     threads = self.threads, 
                                     learning_rate = self.learning_rate,
                                     training_kwds = self.training_kwds,
                                     network_kwds = self.network_kwds,
                                     n_perm = self.n_perm, 
                                     change_perm = self.change_perm,
                                     class_key = self.class_key,
                                     unlabeled_category = self.unlabeled_category,
                                     use_raw_as_output=self.use_raw_as_output)
            
        if self.model_name == 'scanvi':
            self.model = Scanvi(class_key = self.class_key, unlabeled_category=self.unlabeled_category)
            # with method make_net(Dataset), train_net(Dataset)-> training hist, predict_net(Dataset) -> latent_space, corrected_count,        save_net(DR_model_path)

        if self.model_name == 'scarches_scanvi_LCA':
            self.model = ScarchesScanvi_LCA(class_key = self.class_key, unlabeled_category=self.unlabeled_category)
        self.dataset.load_dataset()
        self.dataset.normalize()
        self.dataset.train_split(mode = self.mode,
                            pct_split = self.pct_split,
                            obs_key = self.obs_key,
                            n_keep = self.n_keep,
                            keep_obs = self.keep_obs,
                            obs_subsample = self.obs_subsample,
                            train_test_random_seed = self.train_test_random_seed)
        if self.make_fake:
            self.dataset.fake_annotation(true_celltype=self.true_celltype,
                                    false_celltype=self.false_celltype,
                                    pct_false=self.pct_false,
                                    train_test_random_seed = self.train_test_random_seed)
        if self.n_perm > 1:
            self.dataset.small_clusters_totest()
        print('dataset has been preprocessed')
        self.model.make_net(self.dataset)
        self.DR_hist = self.model.train_net(self.dataset)
        if 'scarches' in self.model_name:
            self.latent_space, self.scarches_combined_emb = self.model.predict_net(self.dataset)
        else: 
            self.latent_space, self.corrected_count = self.model.predict_net(self.dataset)
#         if self.predictor_model == 'MLP':
#             self.predictor = MLP_Predictor(latent_space = self.latent_space,
#                                            predict_key = self.predict_key,
#                                            predictor_hidden_sizes = self.predictor_hidden_sizes,
#                                            predictor_epochs = self.predictor_epochs,
#                                            predictor_batch_size = self.predictor_batch_size,
#                                            predictor_activation = self.predictor_activation,
#                                            unlabeled_category = self.unlabeled_category)
#             self.predictor.preprocess_one_hot()
#             self.predictor.build_predictor()
#             self.predictor.train_model()
#             self.predictor.predict_on_test()
#             self.pred_hist = self.predictor.train_history
#             self.predicted_class = self.predictor.y_pred
#             self.latent_space.obs[f'{self.class_key}_pred'] = self.predicted_class
        self.run_done = True
    
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

        
    def save_results(self):
        if not os.path.isdir(self.result_path):
            os.makedirs(self.result_path)
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
        if self.predict_done:
            with open(self.pred_history_path, 'wb') as file_pi:
                pickle.dump(self.pred_hist.history, file_pi)
        if self.run_done:
            self.write_run_log()
        if self.predict_done:
            self.write_predict_log()
        if self.umap_done:
            self.write_umap_log()


    def load_results(self):
        if os.path.isdir(self.result_path):
            self.latent_space = sc.read_h5ad(self.adata_path)
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