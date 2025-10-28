docker run -it \
    --volume /mnt/share/chufan:/root/af_input \
    --volume /mnt/share/chufan:/root/af_output \
    --volume <MODEL_PARAMETERS_DIR>: /root/models \
    --volume /data/AlphaFold/PRODB:/root/public_databases \
    --gpus all \
    alphafold3 \
python run_alphafold.py \
    --json_path=/mnt/share/chufan/2PV7_input.json \
    --model_dir=/data/AlphaFold/alphafold3/src/alphafold3/model \
    --output_dir=/mnt/share/chufan
