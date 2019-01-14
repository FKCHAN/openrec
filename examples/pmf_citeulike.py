from openrec import ModelTrainer
from openrec.utils import Dataset
from openrec.recommenders import PMF
from openrec.utils.evaluators import NDCG, AUC, Recall
from openrec.utils.samplers import StratifiedPointwiseSampler
from openrec.utils.samplers import EvaluationSampler
import dataloader
import numpy as np

raw_data = dataloader.load_citeulike()
dim_embed = 50
total_iter = int(1e5)
batch_size = 1000
eval_iter = 1000
save_iter = eval_iter

train_dataset = Dataset(raw_data['train_data'], raw_data['total_users'], raw_data['total_items'], name='Train')
val_dataset = Dataset(raw_data['val_data'], raw_data['total_users'], raw_data['total_items'], name='Val')
test_dataset = Dataset(raw_data['test_data'], raw_data['total_users'], raw_data['total_items'], name='Test')

train_sampler = StratifiedPointwiseSampler(pos_ratio=0.2, batch_size=batch_size, dataset=train_dataset, num_process=5)
val_sampler = EvaluationSampler(batch_size=batch_size, dataset=val_dataset, excl_datasets=[train_dataset, test_dataset])
test_sampler = EvaluationSampler(batch_size=batch_size, dataset=test_dataset, excl_datasets=[train_dataset, val_dataset])

model = PMF(batch_size=batch_size, 
            total_users=train_dataset.total_users(), 
            total_items=train_dataset.total_items(), 
            dim_user_embed=dim_embed, 
            dim_item_embed=dim_embed, 
            serve_mode='all', 
            save_model_dir='pmf_recommender/',
            summary_dir='pmf_summary/',
            train=True, serve=True)

ndcg_evaluator = NDCG(ndcg_at=[50, 100])
recall_evaluator = Recall(recall_at=[50, 100])
auc_evaluator = AUC()
model_trainer = ModelTrainer(model=model)

def train_iter_func(model, _input, step, write_summary):
    
    # lr = 0.001 / (10**(step // 30000))
    # _input['lr'] = lr
    return np.sum(model.train(_input, step=step, 
                              write_summary=write_summary)['losses'])
    
model_trainer.train(total_iter=total_iter, eval_iter=eval_iter, 
                    save_iter=save_iter, train_sampler=train_sampler, 
                    eval_samplers=[val_sampler, test_sampler], 
                    evaluators=[ndcg_evaluator, auc_evaluator, recall_evaluator], 
                    train_iter_func=train_iter_func)
