import time
import json
import hmac
import base64
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from requests import Request, Session, Response


class CoinFLEXClient:
    def __init__(self, base_url, api_key=None, api_secret=None) -> None:
        self._session = Session()
        self._base_url = base_url
        self._short_url = self._base_url.replace('https://', '')
        self._api_key = api_key
        self._api_secret = api_secret

    def _get(self, path: str, params: [str, Dict[str, Optional[str]]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[str] = None) -> Any:
        return self._request('POST', path, data=params)

    def _delete(self, path: str, params: Optional[str] = None) -> Any:
        return self._request('DELETE', path, data=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._base_url + path, **kwargs)
        self._authenticate(request)
        prepared = request.prepare()
        response = self._session.send(prepared)
        return self._process_response(response)

    def _authenticate(self, request: Request) -> None:
        ts = str(datetime.utcnow().isoformat())
        nonce = str(int(time.time() * 1000))
        prepared = request.prepare()
        split = ''
        if '?' in prepared.path_url:
            split = prepared.path_url.split('?')
            prepared.body = split[1]
        if prepared.body:
            if split:
                msg_string = f'{ts}\n{nonce}\n{prepared.method}\n{self._short_url}\n{split[0]}\n{prepared.body}'
            else:
                msg_string = f'{ts}\n{nonce}\n{prepared.method}\n{self._short_url}\n{prepared.path_url}\n{prepared.body}'
        else:
            msg_string = f'{ts}\n{nonce}\n{prepared.method}\n{self._short_url}\n{prepared.path_url}\n'

        print(msg_string)

        signature = base64.b64encode(
            hmac.new(
                self._api_secret.encode(),
                msg_string.encode(),
                hashlib.sha256
            ).digest()).decode()

        request.headers = {'Content-Type': 'application/json', 'AccessKey': self._api_key,
                           'Timestamp': ts, 'Signature': signature, 'Nonce': nonce}
        # print(request.headers)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not response.status_code == 200:
                # raise Exception(data)
                print(response.status_code)
            return data

    # ----------------- #
    # Private Endpoints #
    # ----------------- #

    def get_account_info(self) -> dict:
        return self._get('/v1/accounts')

    def get_wallet_history(self, subAcc=None, transfer_type=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/wallet-history',
                         {'subAcc': subAcc,
                          'type': transfer_type,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_balances(self, asset=None):
        return self._get('/v1/balances',
                         {'asset': asset})

    def get_trade_history(self, marketCode=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/trades',
                         {'marketCode': marketCode,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_order_history(self, marketCode=None, orderId=None, clientOrderId=None, limit=None, startTime=None,
                          endTime=None):  # TODO fix this one
        return self._get('/v1/orders/history',
                         {'orderId': orderId,
                          'clientOrderId': clientOrderId,
                          'marketCode': marketCode,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_working_orders(self, marketCode=None, orderId=None, clientOrderId=None):  # TODO fix this one
        return self._get('/v1/orders/working',
                         {'marketCode': marketCode,
                          'orderId': orderId,
                          'clientOrderId': clientOrderId,
                          })

    def place_order(self, recvWindow=None, timestamp=None, responseType=None, clientOrderId=None, marketCode=None,
                    side=None, quantity=None, timeInForce=None, orderType=None, price=None, stopPrice=None,
                    limitPrice=None):
        return self._post('/v1/orders/place',
                          json.dumps({'recvWindow': recvWindow,
                                      'timestamp': timestamp,
                                      'responseType': responseType,
                                      'orders': [{
                                          'clientOrderId': clientOrderId,
                                          'marketCode': marketCode,
                                          'side': side,
                                          'quantity': quantity,
                                          'timeInForce': timeInForce,
                                          'orderType': orderType,
                                          'price': price,
                                          'stopPrice': stopPrice,
                                          'limitPrice': limitPrice,
                                      }]
                                      }
                                     ))

    def place_stop_order(self, recvWindow=None, timestamp=None, responseType=None, clientOrderId=None, marketCode=None,
                    side=None, quantity=None, timeInForce=None, orderType=None, price=None, stopPrice=None):
        return self._post('/v1/orders/place',
                          json.dumps({'recvWindow': recvWindow,
                                      'timestamp': timestamp,
                                      'responseType': responseType,
                                      'orders': [{
                                          'clientOrderId': clientOrderId,
                                          'marketCode': marketCode,
                                          'side': side,
                                          'quantity': quantity,
                                          'timeInForce': timeInForce,
                                          'orderType': orderType,
                                          'price': price,
                                          'stopPrice': stopPrice,
                                      }]
                                      }
                                     ))

    def cancel_order(self, recvWindow=None, timestamp=None, responseType=None, orderId=None, clientOrderId=None,
                     marketCode=None, ):
        return self._delete('/v1/orders/cancel',
                            json.dumps(
                                {'recvWindow': recvWindow,
                                 'timestamp': timestamp,
                                 'responseType': responseType,
                                 'orders': [{
                                     'marketCode': marketCode,
                                     'orderId': orderId,
                                     'clientOrderId': clientOrderId
                                 }],
                                 }))

    def modify_order(self):
        pass

    def cancel_all(self, marketCode=None):
        return self._delete('/v1/orders/cancel-all',
                            json.dumps({'marketCode': marketCode}))

    def get_funding_payments(self, marketCode=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/funding',
                         {'marketCode': marketCode,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def mint_flexAsset(self, asset=None, quantity=None):
        return self._post('/v1/flexasset/mint',
                          json.dumps({'asset': asset,
                                      'quantity': quantity}))

    def redeem_flexAsset(self, asset=None, quantity=None, redeem_type=None):
        return self._post('/v1/flexasset/redeem',
                          json.dumps({'asset': asset,
                                      'quantity': quantity,
                                      'type': redeem_type}))

    def get_mint_history(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/flexasset/mint',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_redeem_history(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/flexasset/redeem',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_flexAsset_interest_history(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/flexasset/earned',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_note_interest_history(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/notetoken/earned',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def withdraw(self, asset=None, network=None, address=None, memo=None, quantity=None, externalFee=None, tfaType=None,
                 code=None):
        return self._post('/v1/withdrawal',
                          json.dumps({
                              'asset': asset,
                              'network': network,
                              'address': address,
                              'memo': memo,
                              'quantity': quantity,
                              'externalFee': externalFee,
                              'tfaType': tfaType,
                              'code': code
                          }
                          ))

    def get_withdrawal_history(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/withdrawal',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_deposit_address(self, asset=None, network=None):
        return self._get('/v1/deposit-addresses',
                         {'asset': asset,
                          'network': network})

    def get_deposit_history(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get('/v1/deposit',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def list_withdrawal_addresses(self, asset=None, network=None):
        return self._get('/v1/withdrawal-addresses',
                         {'asset': asset,
                          'network': network})

    def withdrawal_fee_estimate(self, asset=None, network=None, address=None, memo=None, quantity=None,
                                externalFee=None):
        return self._get('/v1/withdrawal-fee',
                         {'asset': asset,
                          'network': network,
                          'address': address,
                          'memo': memo,
                          'quantity': quantity,
                          'externalFee': externalFee,
                          })

    def sub_account_transfer(self, asset=None, quantity=None, fromAccount=None, toAccount=None):
        return self._post('/v1/transfer',
                          json.dumps({'asset': asset,
                                      'quantity': quantity,
                                      'fromAccount': fromAccount,
                                      'toAccount': toAccount}))

    def transfer_history(self, asset=None, limit=None, startTime=None, endTime=None):  # TODO: might take "id" param
        return self._get('/v1/transfer',
                         {'asset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime})

    def get_orders(self, market: Optional[str] = None, order_id: Optional[int] = None,
                   client_id: Optional[int] = None, limit: Optional[int] = None,
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> dict:
        return self._get(f'/v1.1/orders',
                         {'marketCode': market,
                          'orderId': order_id,
                          'clientId': client_id,
                          'limit': limit,
                          'startTime': start_time,
                          'endTime': end_time})

    def bulk_modify_order(self, recv_window, response_type, orders: List[dict]):
        return self._post('/v1/orders/modify',
                          json.dumps({'recvWindow': recv_window,
                                      'responseType': response_type,
                                      'timestamp': time.time() * 1000,
                                      'orders': orders
                                      }))

    def bulk_cancel_order(self, recv_window, response_type, orders: List[dict]):
        return self._delete('/v1/orders/cancel',
                            json.dumps({'recvWindow': recv_window,
                                        'responseType': response_type,
                                        'timestamp': time.time() * 1000,
                                        'orders': orders
                                        }))

    # ---------------- #
    # Public Endpoints #
    # ---------------- #
    def get_tickers(self, marketCode=None) -> List[dict]:
        return self._get('/v1/tickers',
                         {'marketCode': marketCode})

    def get_candles(self, marketCode=None, timeframe=None, limit=None, startTime=None, endTime=None) -> List[dict]:
        return self._get('/v1/candles',
                         {'marketCode': marketCode,
                          'timeframe': timeframe,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime
                          })

    def get_depth(self, marketCode=None, level=None) -> List[dict]:
        return self._get('/v1/depth',
                         {'marketCode': marketCode,
                          'level': level
                          })

    def get_flexasset_balances(self, asset=None) -> List[dict]:
        return self._get('/v1/flexasset/balances',
                         {'flexasset': asset})

    def get_flexasset_positions(self, asset=None) -> List[dict]:
        return self._get('/v1/flexasset/positions',
                         {'flexasset': asset})

    def get_flexasset_yields(self, asset=None, limit=None, startTime=None, endTime=None):
        return self._get(f'/v1/flexasset/yields',
                         {'flexasset': asset,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime
                          })

    def get_markets(self, marketCode=None) -> dict:
        return self._get('/v1/markets',
                         {'marketCode': marketCode})

    def get_assets(self, asset=None) -> dict:
        return self._get('/v1/assets',
                         {'asset': asset})

    def get_public_trades(self, marketCode=None, limit=None, startTime=None, endTime=None):
        return self._get(f'/v1/exchange-trades',
                         {'marketCode': marketCode,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime
                          })

    def get_wallet(self, type=None, limit=None, startTime=None, endTime=None):
        return self._get(f'/v1/wallet',
                         {'type': type,
                          'limit': limit,
                          'startTime': startTime,
                          'endTime': endTime
                          })


if __name__ == '__main__':
    api_key = ""
    api_secret = ""

    # base_url = 'https://v2stgapi.coinflex.com'
    base_url = 'https://stgapi.coinflex.us'

    rest = CoinFLEXClient(base_url, api_key, api_secret)
