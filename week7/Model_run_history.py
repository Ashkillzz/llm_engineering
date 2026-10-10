import wandb
api = wandb.Api()
run = api.run("/ashkillzz-vellore-institute-of-technology/price/runs/ygu7d083")

print(run.history())