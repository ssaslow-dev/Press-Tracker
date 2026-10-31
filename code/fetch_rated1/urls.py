import json,sys
L='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib'
J=[json.loads(l) for l in open(f'{L}/work/jobs/fetch_rated_1.jsonl')]
a,b=int(sys.argv[1]),int(sys.argv[2])
print(json.dumps([J[i]['url'] for i in range(a,b)]))
