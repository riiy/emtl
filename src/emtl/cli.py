import argparse

from .utils import get_logger

logger = get_logger(__name__)


logger.info("cli")
parser = argparse.ArgumentParser(prog="emt", description="东方财富交易接口", epilog="东方财富交易接口")
parser.add_argument("-u", "--user", required=False)
parser.add_argument("-p", "--password", required=False)
group = parser.add_mutually_exclusive_group()
group.add_argument("-b", "--buy", help="买入股票，格式为：代码－价格－数量。例子买入一手平安银行：000001-10.21-100")
group.add_argument("-s", "--sell", help="卖出股票，格式为：代码－价格－数量。卖一手平安银行：000001-10.21-100")
group.add_argument("-q", "--query", type=str, choices=["asset", "order", "trade"], help="查询账户的资产、挂单、成交")


def run(args=None):
    logger.info(args)
    args = parser.parse_args(args=args)
    logger.info(args)
    print(args.user, args.password)
    parser.exit(0)


if __name__ == "__main__":
    run()
