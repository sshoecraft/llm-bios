echo "/clear" | shepherd --backend cli --api-base localhost:9999
shepherd --backend cli --api-base localhost:9999 --prompt "$(cat prompts/stage1-format.txt)"
shepherd --backend cli --api-base localhost:9999 --prompt "$(cat prompts/stage2-compiler.txt)"
shepherd --backend cli --api-base localhost:9999 --prompt "$(cat prompts/stage3-selfcompile-2.txt)"
shepherd --backend cli --api-base localhost:9999 --prompt "$(cat prompts/stage5-build-bios.txt; cat template.md; cat prompts/stage5-build-post.txt)"
shepherd --backend cli --api-base localhost:9999 --prompt "$(cat prompts/stage6-preamble.txt)" > session.log
awk '/---BEGIN PREAMBLE---/{flag=1; next} /---END PREAMBLE---/{flag=0} flag' session.log > bios.txt
awk '/---BEGIN BIOS---/{flag=1; next} /---END BIOS---/{flag=0} flag' session.log >> bios.txt
