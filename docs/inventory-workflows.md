# Inventory workflows

## Product catalogue

Add a product with a unique SKU, display name, unit, reorder level and an
optional opening stock quantity. Opening stock is recorded as a ledger movement;
the application does not assume or invent stock balances. Products can be
deactivated without deleting their movement history.

## Stock movements

- Receipt: adds a positive quantity.
- Issue: subtracts a positive quantity and is rejected if it would make
  stock negative.
- Positive adjustment: adds a positive correction quantity.
- Opening balance: recorded when a product is first created with non-zero
  opening stock.
- Order fulfilment: deducts the quantity of each linked product line.
- Stocktake adjustment: records the difference between the current balance
  and a confirmed physical count.

Each movement stores its type, signed quantity change, resulting balance,
timestamp, optional reference and notes. Product balance and ledger entry are
committed together.

## Physical stocktake

The stocktake workflow captures the recorded quantity and the user's physical
count. The variance is shown for review. Nothing changes until the user confirms
reconciliation. Reconciliation updates all affected product balances and writes
ledger movements in one transaction. If stock changes after the count snapshot
is taken, reconciliation is blocked to avoid overwriting newer receipts, issues
or order fulfilments; start a new stocktake instead.

## Order integration

Order lines can optionally be linked to a catalogue SKU. Freeform lines are
treated as services or non-stock items. When an order transitions from
Processing to Fulfilled, the application groups linked quantities by product,
checks availability and deducts stock in the same transaction as the status
change. If any product has insufficient stock, the entire operation rolls back.
The unique order/product movement constraint and terminal order status prevent
a second deduction through the normal workflow.

A fulfilled order cannot currently be cancelled or automatically restocked.
Returns and reversals need a future controlled workflow.

## Precision and limits

Quantities are stored to three decimal places. SKU uniqueness is scoped to the
current business workspace. The current interface uses the first configured
workspace and does not yet provide multi-workspace selection.
