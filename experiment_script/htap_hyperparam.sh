#!/bin/sh
#
#SBATCH --account=cell     # The account name for the job.
#SBATCH --job-name=htap_hyperparam       # The job name.
#SBATCH --gres=gpu:1           # Request 1 gpu (Up to 2 gpus per GPU node)
#SBATCH --partition=gpu
#SBATCH --time=20:00:00           # The time the job will take to run in D-HH:MM
#SBATCH --output=/home/acollin/htap_hyperparam.log # Important to retrieve the port where the notebook is running, if not included a slurm file with the job-id will be outputted. 


working_dir="/home/acollin/dca_permuted_workflow"
singularity_working_dir="/data/dca_permuted_workflow"
singularity_path=$working_dir"/singularity_scPermut.sif"

singularity exec --nv --bind $working_dir:$singularity_working_dir $singularity_path


singularity exec --nv --bind $working_dir:$singularity_working_dir $singularity_path python /home/acollin/dca_permuted_workflow/workflow/workflow_hp.py --dataset_name htap_final_by_batch --class_key celltype --batch_key donor --use_hvg 5000 --mode entire_condition --obs_key donor --keep_obs PRC_5 PAH_675093 PRC_2 --training_scheme training_scheme_1