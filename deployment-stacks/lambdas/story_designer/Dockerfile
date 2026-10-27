FROM public.ecr.aws/lambda/python:3.12

COPY packages/sanora-contracts /tmp/sanora-contracts
RUN python -m pip install \
        --no-cache-dir \
        --upgrade \
        --force-reinstall \
        --only-binary=:all: \
        /tmp/sanora-contracts \
        --target "${LAMBDA_TASK_ROOT}" \
    && PYTHONPATH="${LAMBDA_TASK_ROOT}" python -c \
        "from pydantic_core import ArgsKwargs; from sanora_contracts import StoryDesignerResponse" \
    && rm -rf /tmp/sanora-contracts

COPY deployment-stacks/lambdas/story_designer/story_designer.py ${LAMBDA_TASK_ROOT}/

CMD ["story_designer.handler"]
