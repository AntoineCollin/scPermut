#!/bin/sh
#
#SBATCH --account=cell     # The account name for the job.
#SBATCH --job-name=cb_htap_1      # The job name.
#SBATCH --gres=gpu:1           # Request 1 gpu (Up to 2 gpus per GPU node)
#SBATCH --partition=gpu
#SBATCH --nodelist=gpu03
#SBATCH --time=35:00:00           # The time the job will take to run in D-HH:MM
#SBATCH --output=/home/cbecavin/temp/htap_hyperparam.log # Important to retrieve the port where the notebook is running, if not included a slurm file with the job-id will be outputted. 


working_dir="/home/cbecavin/dca_permuted_workflow"
singularity_working_dir="/data/dca_permuted_workflow"
singularity_path=$working_dir"/singularity/scPermut_gpu_jupyter.sif"
python_script=$working_dir/workflow/scpermut_optimize.py
log_file=$working_dir"/experiment_script/htap_hyperparam_scheme_1.log"

module load singularity

singularity exec --nv --bind $working_dir:$singularity_working_dir $singularity_path python $python_script \
--dataset_name htap_final_by_batch --class_key celltype --batch_key donor --use_hvg 5000 \
--mode entire_condition --obs_key donor --keep_obs PAH_688194 PAH_691048 PAH_693770 PAH_698029 PRC_16 PRC_18 PRC_3 PRC_8 \
--training_scheme training_scheme_1 --hparam_path htap_r2_sch1 &> $log_file
