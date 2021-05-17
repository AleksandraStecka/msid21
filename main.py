import requests
import time


class Endpoint:

    def __init__(self, name, url, taker_fee, transfer_fee):
        self.__name = name
        self.__url = url
        self.__taker_fee = taker_fee
        self.__transfer_fee = transfer_fee

    @property
    def name(self):
        return self.__name

    @property
    def url(self):
        return self.__url

    @property
    def taker_fee(self):
        return self.__taker_fee

    @property
    def transfer_fee(self):
        return self.__transfer_fee


class Apis:

    def __init__(self):
        self.__bitbay = Endpoint("BITBAY", "https://bitbay.net/API/Public/{}{}/orderbook.json", 0.043, 0.0005)
        self.__bittrex = Endpoint("BITTREX",
                                  "https://api.bittrex.com/api/v1.1/public/getorderbook?market={}-{}&type=both",
                                  0.025, 0.005)
        self.__base_currency = "USD"
        self.__crypto_currency = "BTC"

    @property
    def bitbay(self):
        return self.__bitbay

    @property
    def bittrex(self):
        return self.__bittrex

    @property
    def base_currency(self):
        return self.__base_currency

    @property
    def crypto_currency(self):
        return self.__crypto_currency


APIS = Apis()
SINGLE_OFFER = 1
SLEEP_TIME = 5


def get_response(url):
    api_response = requests.get(url)
    if 200 <= api_response.status_code <= 299:
        return api_response.json()
    else:
        print("Could not connect to API.", api_response.reason)
        return None


def get_offers(api_name, no_of_offers):
    if api_name == APIS.bitbay.name:
        all_offers = get_response(APIS.bitbay.url.format(APIS.crypto_currency, APIS.base_currency))
        if all_offers is not None:
            return {'bids': (all_offers['bids'][:no_of_offers]), 'asks': (all_offers['asks'][:no_of_offers])}
    else:
        all_offers = get_response(APIS.bittrex.url.format(APIS.base_currency, APIS.crypto_currency))
        if all_offers is not None:
            tmp = {'bids': [], 'asks': []}
            for i in range(no_of_offers):
                bids_list = list(all_offers['result']['buy'][i].values())
                bids_list.reverse()
                asks_list = list(all_offers['result']['sell'][i].values())
                asks_list.reverse()
                tmp['bids'].append(bids_list)
                tmp['asks'].append(asks_list)
            return tmp


def get_buy_sell_ratio(api_name_1, api_name_2, offer_type):
    offer_api_1 = get_offers(api_name_1, SINGLE_OFFER)
    offer_api_2 = get_offers(api_name_2, SINGLE_OFFER)
    if offer_api_1 is None or offer_api_2 is None:
        return None
    else:
        return (offer_api_1[offer_type][0][0] - offer_api_2[offer_type][0][0]) / offer_api_1[offer_type][0][0] * 100


def get_arbitrage_ratio(api_name_1, api_name_2):
    offer_api_1 = get_offers(api_name_1, SINGLE_OFFER)
    offer_api_2 = get_offers(api_name_2, SINGLE_OFFER)
    if offer_api_1 is None or offer_api_2 is None:
        return None
    else:
        return (offer_api_2['bids'][0][0] - offer_api_1['asks'][0][0]) / offer_api_2['bids'][0][0] * 100


def include_fees(api_name, fee_name, cost):
    if fee_name == "taker_fee":
        if api_name == APIS.bitbay.name:
            return cost * (1 + APIS.bitbay.taker_fee)
        else:
            return cost * (1 + APIS.bittrex.taker_fee)
    else:
        if api_name == APIS.bitbay.name:
            return cost - APIS.bitbay.transfer_fee
        else:
            return cost - APIS.bittrex.transfer_fee


def get_arbitrage_info(api_name_1, api_name_2):
    offer_api_1 = get_offers(api_name_1, SINGLE_OFFER)
    offer_api_2 = get_offers(api_name_2, SINGLE_OFFER)
    amount = min(offer_api_1['asks'][0][1], offer_api_2['bids'][0][1])
    spent = include_fees(api_name_1, "taker", offer_api_1['asks'][0][0]) * amount
    earned = include_fees(api_name_2, "transfer", offer_api_2['bids'][0][0]) * amount
    return {'amount': amount, 'USD': earned - spent, 'profit': (earned - spent) / spent * 100}


def print_ex1(api_name_1, api_name_2):
    print("----EXERCISE 1:")
    print("\ta)", f'{api_name_1} to {api_name_2} buy ratio for {APIS.crypto_currency}{APIS.base_currency}: '
                  f'{get_buy_sell_ratio(api_name_1, api_name_2, "bids"):.2f}%')
    print("\tb)", f'{api_name_1} to {api_name_2} sell ratio for {APIS.crypto_currency}{APIS.base_currency}: '
                  f'{get_buy_sell_ratio(api_name_1, api_name_2, "asks"):.2f}%')
    print("\tc)", f'{api_name_1} to {api_name_2} arbitrage ratios for {APIS.crypto_currency}{APIS.base_currency}:')
    print(f'\tBuy at {api_name_1}, sell at {api_name_2}: {get_arbitrage_ratio(api_name_1, api_name_2):.2f}%')
    print(f'\tBuy at {api_name_2}, sell at {api_name_1}: {get_arbitrage_ratio(api_name_2, api_name_1):.2f}%')


def print_ex2(api_name_1, api_name_2):
    print("----EXERCISE 2:")
    buy_at_1_sell_at_2 = get_arbitrage_info(api_name_1, api_name_2)
    sell_at_1_buy_at_2 = get_arbitrage_info(api_name_2, api_name_1)
    print(f'\tBuy at {api_name_1}, sell at {api_name_2}:\n\tResource quantity: {buy_at_1_sell_at_2["amount"]}, '
          f'profit: {buy_at_1_sell_at_2["profit"]:.2f}%, profit in USD: {buy_at_1_sell_at_2["USD"]:.2f}$')
    print(f'\tBuy at {api_name_2}, sell at {api_name_1}:\n\tResource quantity: {sell_at_1_buy_at_2["amount"]}, '
          f'profit: {sell_at_1_buy_at_2["profit"]:.2f}%, profit in USD: {sell_at_1_buy_at_2["USD"]:.2f}$')


def print_ex1_ex2(api_name_1, api_name_2):
    while True:
        print_ex1(api_name_1, api_name_2)
        print_ex2(api_name_1, api_name_2)
        print("------------------------")
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    try:
        print_ex1_ex2(APIS.bitbay.name, APIS.bittrex.name)  # endless loop - refresh every 5 sec
    except requests.exceptions:
        print("Connection to APIs failed.")
