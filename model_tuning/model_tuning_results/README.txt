====== model_tuning_results =======
This folder contained the saved tuned weights for Llama 31.:8b on the provided datasets

====== Tuned Parameter Folders ======
llama3_depress_first_training_30%split_seed30
llama3.1_depress_first_training_10%split_seed42
llama3_emodepressed_trained_1.0_10%_seed42

These files are too large for GITHUB so they are hosted else where, look in the wiki under "Trained Weights".

====== Converting to .gguf and merging to use in Ollama ======
convert_to_gguf.py
EXAMPLE USAGE: python .\convert_to_gguf.py ".\llama3_emodepressed_trained_1.0_10%_seed42" ".\exports\llama3_emodepressed_merged"

This file takes one of the tuned parameter folders as an argument and an output folder wehere the model is merged with the trained weights.

====== Modelfiles for Ollama Usage ======
ollama_model_files
EXMAPLE USAGE: ollama create emoDepressed_8bit -f .\Model_files\Modelfile_Binary

Contains the used in testing modelfiles for importing the merged models into Ollama.
Make sure to change the path in the model file to that of your merged model folder once created.